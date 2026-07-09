import { Navigate } from "react-router";
import { useSelector } from "react-redux";
import { selectIsAuthenticated } from "@/store/slices/authSlice";

/**
 * ProtectedRoute — Bảo vệ các route yêu cầu đăng nhập.
 * Nếu chưa authenticate → redirect về /login.
 */
function ProtectedRoute({ children }) {
  const isAuthenticated = useSelector(selectIsAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
