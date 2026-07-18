import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { useDispatch } from "react-redux";
import { loginWithGoogleCode } from "@/store/slices/authSlice.js";

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

    if (error) {
      navigate("/login", {
        replace: true,
        state: { authError: errorDescription || "Đăng nhập Google thất bại." },
      });
      return;
    }
    if (!code) {
      navigate("/login", { replace: true });
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
