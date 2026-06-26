import SmartSidebar from "../components/layout/SmartSidebar.jsx";
import ChatArea from "../components/chat/ChatArea.jsx";

function SmartdocPage() {
  return (
    <div className="flex h-full w-full overflow-hidden">
      <SmartSidebar />

      <ChatArea />
    </div>
  );
}

export default SmartdocPage;
