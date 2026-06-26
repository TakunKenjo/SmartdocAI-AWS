import { Routes, Route } from "react-router";
import SmartdocPage from "@/features/smartdocs/pages/SmartdocPage.jsx";
import { ThemeProvider } from "@/contexts/ThemeContext.jsx";
import { Toaster } from "@/components/ui/sonner";

function App() {
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
