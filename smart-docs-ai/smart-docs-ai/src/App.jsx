import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Routes, Route, Navigate } from "react-router";
import SmartdocPage from "@/features/smartdocs/pages/SmartdocPage.jsx";
import LoginPage from "@/features/auth/pages/LoginPage.jsx";
import RegisterPage from "@/features/auth/pages/RegisterPage.jsx";
import ProtectedRoute from "@/features/auth/components/ProtectedRoute.jsx";
import ProfilePage from "@/features/profile/pages/ProfilePage.jsx";
import { ThemeProvider } from "@/contexts/ThemeContext.jsx";
import { Toaster } from "@/components/ui/sonner";
import { checkOllamaStatus } from "@/store/slices/smartdocSlice";
import { getProfile, selectIsAuthenticated } from "@/store/slices/authSlice";

function App() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector(selectIsAuthenticated);

  useEffect(() => {
    // Warm-up Lambda khi vừa mở trang
    dispatch(checkOllamaStatus());

    // Load avatar + thông tin đầy đủ từ DynamoDB ngay khi đã đăng nhập
    // (bao gồm cả trường hợp reload trang — session từ sessionStorage)
    if (isAuthenticated) {
      dispatch(getProfile());
    }
  }, [dispatch, isAuthenticated]);

  return (
    <ThemeProvider>
      <Routes>
        {/* Mặc định redirect về /login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Public routes — auth */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected route — trang chính SmartDoc */}
        <Route
          path="/app/*"
          element={
            <ProtectedRoute>
              <SmartdocPage />
            </ProtectedRoute>
          }
        />

        {/* Protected route — Hồ sơ cá nhân */}
        <Route
          path="/app/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
      </Routes>
      <Toaster richColors position="top-right" />
    </ThemeProvider>
  );
}

export default App;
