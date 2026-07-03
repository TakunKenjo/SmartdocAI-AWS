import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { Routes, Route } from "react-router";
import SmartdocPage from "@/features/smartdocs/pages/SmartdocPage.jsx";
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
        <Route path="/*" element={<SmartdocPage />} />
      </Routes>
      <Toaster richColors position="top-right" />
    </ThemeProvider>
  );
}

export default App;

