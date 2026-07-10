import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { Routes, Route, Navigate } from "react-router";
import SmartdocPage from "@/features/smartdocs/pages/SmartdocPage.jsx";
import LoginPage from "@/features/auth/pages/LoginPage.jsx";
import RegisterPage from "@/features/auth/pages/RegisterPage.jsx";
import ProtectedRoute from "@/features/auth/components/ProtectedRoute.jsx";
import { ThemeProvider } from "@/contexts/ThemeContext.jsx";
import { Toaster } from "@/components/ui/sonner";
import { checkOllamaStatus } from "@/store/slices/smartdocSlice";

function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    // Tự động gửi request đánh thức Lambda (Warm-up) khi vừa mở trang web
    dispatch(checkOllamaStatus());
  }, [dispatch]);

  return (
    <ThemeProvider>
      <Routes>
        {/* Mặc định redirect về /login */}
        {/* <Route path="/" element={<Navigate to="/login" replace />} /> */}

        {/* Public routes — auth */}
        {/* <Route path="/login" element={<LoginPage />} /> */}
        {/* <Route path="/register" element={<RegisterPage />} /> */}

        {/* Protected route — trang chính SmartDoc */}
        <Route
          path="/app/*"
          element={
            // <ProtectedRoute>
            <SmartdocPage />
            // </ProtectedRoute>
          }
        />
      </Routes>
      <Toaster richColors position="top-right" />
    </ThemeProvider>
  );
}

export default App;
