const COGNITO_DOMAIN =
  "https://smartdocai-fayrun2026.auth.us-east-1.amazoncognito.com";
const CLIENT_ID = "63f74h4dj78kqihhoimv4acl8a";
const getRedirectUri = () => `${window.location.origin}/auth/callback`;

// Tạo URL để chuyển hướng người dùng sang màn hình đăng nhập Google (qua Cognito Hosted UI)
export const getGoogleLoginUrl = () => {
  const params = new URLSearchParams({
    identity_provider: "Google",
    client_id: CLIENT_ID,
    response_type: "code",
    scope: "openid email profile",
    redirect_uri: getRedirectUri(),
    prompt: "select_account",
  });
  return `${COGNITO_DOMAIN}/oauth2/authorize?${params.toString()}`;
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
