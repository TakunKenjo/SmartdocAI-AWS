import { useRef, useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { BrainCircuit, ChevronDown, Loader2, Menu } from "lucide-react";
import {
  selectChatHistory,
  selectIsChatLoading,
  selectProcessedFiles,
} from "@/store/slices/smartdocSlice.js";
import ChatMessage from "./ChatMessage.jsx";
import WelcomeHero from "./WelcomeHero.jsx";
import SearchSettings from "./SearchSettings.jsx";
import ChatInput from "./ChatInput.jsx";

/**
 * ChatArea — Vùng chat chính: messages list + settings expander + input bar
 * Bao gồm auto-scroll xuống cuối, loading indicator, scroll-to-bottom button
 * Nhận prop onOpenSidebar — gọi khi nhấn hamburger menu trên mobile
 */
function ChatArea({ onOpenSidebar = () => {} }) {
  const chatHistory = useSelector(selectChatHistory);
  const isLoading = useSelector(selectIsChatLoading);
  const processedFiles = useSelector(selectProcessedFiles);

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatHistory.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory]);

  const handleScroll = () => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollBtn(distFromBottom > 200);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const hasDocs = processedFiles.length > 0;
  const hasMessages = chatHistory.length > 0;

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-slate-50 dark:bg-slate-950">

      {/* ── Mobile top bar — chỉ hiện trên mobile (< md) — ẩn trên desktop —— */}
      <div className="flex md:hidden flex-shrink-0 items-center justify-between px-3 py-2.5 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center gap-2.5">
          {/* Hamburger button */}
          <button
            onClick={onOpenSidebar}
            className="h-9 w-9 flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Mở menu"
            id="mobile-menu-btn"
          >
            <Menu className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>

          {/* Brand */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm shadow-blue-600/30">
              <BrainCircuit className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold text-sm text-slate-900 dark:text-slate-50 leading-none">SmartDocAI</span>
          </div>
        </div>

        {/* Right side placeholder — có thể thêm nút sau */}
        <div className="w-9" aria-hidden="true" />
      </div>
      {/* ────────────────────────────────────────────── */}

      {/* ── Messages Area ── */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto relative"
      >
        {!hasMessages ? (
          /* Welcome screen */
          <WelcomeHero hasDocs={hasDocs} />
        ) : (
          /* Chat messages */
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
            {chatHistory.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex gap-3 justify-start animate-in slide-in-from-bottom-2 duration-300">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <BrainCircuit className="h-4 w-4 text-white" />
                </div>
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                  <div className="flex gap-1 items-center">
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

       

        {/* Scroll-to-bottom button */}
        {showScrollBtn && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-4 right-4 w-9 h-9 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full shadow-md flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
          >
            <ChevronDown className="h-4 w-4 text-slate-500" />
          </button>
        )}
      </div>

      {/* ── Search Settings Expander ── */}
      <div className="flex-shrink-0 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <button
          onClick={() => setSettingsOpen(!settingsOpen)}
          className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          id="search-settings-toggle"
        >
          <span>⚙ Cài đặt tìm kiếm nâng cao</span>
          <ChevronDown
            className={`h-4 w-4 transition-transform duration-200 ${settingsOpen ? "" : "rotate-180"}`}
          />
        </button>

        {settingsOpen && (
          <div className="border-t border-slate-100 dark:border-slate-800 animate-in slide-in-from-top-2 duration-200">
            <SearchSettings />
          </div>
        )}
      </div>

      {/* ── Chat Input ── */}
      <ChatInput />
    </div>
  );
}

export default ChatArea;
