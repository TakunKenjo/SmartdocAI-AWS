const COGNITO_DOMAIN =
  "https://smartdocai-fayrun2026.auth.us-east-1.amazoncognito.com";
const CLIENT_ID = "63f74h4dj78kqihhoimv4acl8a";
const getRedirectUri = () => `${window.location.origin}/auth/callback`;
const OAUTH_STATE_KEY = "oauth_state";

// Tạo URL để chuyển hướng người dùng sang màn hình đăng nhập Google (qua Cognito Hosted UI)
// Kèm theo tham số "state" ngẫu nhiên để chống tấn công CSRF (login CSRF / OAuth code injection):
// - Sinh ra 1 giá trị ngẫu nhiên, lưu tạm vào sessionStorage của trình duyệt hiện tại.
// - Khi Cognito redirect về /auth/callback, "state" phải được echo lại y nguyên.
// - Nếu không khớp (hoặc bị thiếu) -> có khả năng authorization code bị đánh cắp/giả mạo -> từ chối.
export const getGoogleLoginUrl = () => {
  const state = crypto.randomUUID();
  sessionStorage.setItem(OAUTH_STATE_KEY, state);

  const params = new URLSearchParams({
    identity_provider: "Google",
    client_id: CLIENT_ID,
    response_type: "code",
    scope: "openid email profile",
    redirect_uri: getRedirectUri(),
    prompt: "select_account",
    state,
  });
  return `${COGNITO_DOMAIN}/oauth2/authorize?${params.toString()}`;
};

// So sánh "state" nhận được từ Cognito callback với giá trị đã lưu trước đó.
// Luôn xóa giá trị đã lưu sau khi kiểm tra (dùng 1 lần) để tránh replay.
export const verifyOAuthState = (returnedState) => {
  const savedState = sessionStorage.getItem(OAUTH_STATE_KEY);
  sessionStorage.removeItem(OAUTH_STATE_KEY);
  return Boolean(savedState) && savedState === returnedState;
};

// Đổi authorization code lấy token thật từ Cognito
export const exchangeCodeForTokens = async (code) => {
  const params = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    code,
    redirect_uri: getRedirectUri(),
  });

  const res = await fetch(`${COGNITO_DOMAIN}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params.toString(),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Đổi code lấy token thất bại: ${errText}`);
  }
  return res.json(); // { id_token, access_token, refresh_token, expires_in, token_type }
};

export const checkGoogleEmailAllowed = async (idToken) => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "";
  const res = await fetch(`${apiBaseUrl}/api/auth/google/check-email`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${idToken}`,
    },
  });

  if (!res.ok) {
    if (res.status === 404 || res.status === 405) {
      console.warn(
        "[GoogleLogin] Backend check-email endpoint chưa sẵn sàng, bỏ qua lớp check phụ.",
      );
      return { success: true, skipped: true };
    }

    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Không thể đăng nhập bằng Google với email này.");
  }

  return res.json();
};

// Giải mã payload JWT — chỉ để đọc claim hiển thị UI (KHÔNG dùng để verify).
// Backend vẫn luôn tự verify chữ ký thật mỗi khi gọi API, không tin dữ liệu này.
export const decodeJwtPayload = (token) => {
  const payload = token.split(".")[1];
  const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
  return JSON.parse(decodeURIComponent(escape(decoded)));
};

// Ghi token vào sessionStorage ĐÚNG định dạng amazon-cognito-identity-js đang dùng,
// để getSessionToken()/axiosConfig.js/ProtectedRoute dùng được luôn, không cần sửa gì thêm.
export const persistCognitoSession = ({
  idToken,
  accessToken,
  refreshToken,
  username,
}) => {
  const prefix = `CognitoIdentityServiceProvider.${CLIENT_ID}`;
  sessionStorage.setItem(`${prefix}.LastAuthUser`, username);
  sessionStorage.setItem(`${prefix}.${username}.idToken`, idToken);
  sessionStorage.setItem(`${prefix}.${username}.accessToken`, accessToken);
  sessionStorage.setItem(`${prefix}.${username}.refreshToken`, refreshToken);
  sessionStorage.setItem(`${prefix}.${username}.clockDrift`, "0");
};
