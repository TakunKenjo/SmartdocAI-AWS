import { useState } from "react";
import SmartSidebar from "../components/layout/SmartSidebar.jsx";
import ChatArea from "../components/chat/ChatArea.jsx";

function SmartdocPage() {
  // Mobile sidebar drawer state — chỉ dùng trên mobile (<md)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-full w-full overflow-hidden relative">

      {/* ── Mobile overlay backdrop ── */}
      {/* Hiện trên mobile khi sidebar mở, click để đóng */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <SmartSidebar
        mobileOpen={mobileSidebarOpen}
        onMobileClose={() => setMobileSidebarOpen(false)}
      />

      <ChatArea onOpenSidebar={() => setMobileSidebarOpen(true)} />
    </div>
  );
}

export default SmartdocPage;
