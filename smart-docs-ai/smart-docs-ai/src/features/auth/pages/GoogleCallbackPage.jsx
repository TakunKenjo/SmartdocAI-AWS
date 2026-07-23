import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { useDispatch } from "react-redux";
import { loginWithGoogleCode } from "@/store/slices/authSlice.js";
import { verifyOAuthState } from "@/api/cognitoOAuth.js";

const normalizeAuthError = (message) => {
  if (!message) return "Đăng nhập Google thất bại.";

  const cleaned = message.replace(/^PreSignUp failed with error\s*/i, "").trim();

  if (cleaned === "An error occurred") {
    return "Không thể đăng nhập bằng Google lúc này. Vui lòng thử lại sau.";
  }

  return cleaned;
};

function GoogleCallbackPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const hasRun = useRef(false); // chặn chạy 2 lần do React StrictMode

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const error = params.get("error");
    const errorDescription = params.get("error_description");
    const returnedState = params.get("state");

    if (error) {
      navigate("/login", {
        replace: true,
        state: { authError: normalizeAuthError(errorDescription) },
      });
      return;
    }
    if (!code) {
      navigate("/login", { replace: true });
      return;
    }

    // Chống CSRF: "state" trả về phải khớp với giá trị đã lưu lúc redirect đi Google.
    // Nếu không khớp (thiếu, bị sửa, hoặc code bị đánh cắp từ 1 phiên login khác)
    // -> từ chối luôn, không đổi code lấy token.
    if (!verifyOAuthState(returnedState)) {
      navigate("/login", {
        replace: true,
        state: {
          authError:
            "Phiên đăng nhập Google không hợp lệ hoặc đã hết hạn. Vui lòng thử lại.",
        },
      });
      return;
    }

    dispatch(loginWithGoogleCode(code))
      .unwrap()
      .then(() => navigate("/app", { replace: true }))
      .catch((msg) => {
        navigate("/login", {
          replace: true,
          state: { authError: msg || "Đăng nhập Google thất bại." },
        });
      });
  }, [dispatch, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-slate-400">Đang xử lý đăng nhập Google...</p>
    </div>
  );
}

export default GoogleCallbackPage;
