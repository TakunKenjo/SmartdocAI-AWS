import { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  sendMessage,
  addUserMessage,
  selectIsChatLoading,
  selectHybridEnabled,
  selectRerankerEnabled,
  selectSelfRagEnabled,
  selectSelfRagConfig,
  selectCoRagEnabled,
  selectCoRagConfig,
  selectActiveFileFilter,
} from "@/store/slices/smartdocSlice.js";
import { toast } from "sonner";

/**
 * ChatInput — Input bar cố định ở cuối màn hình
 * Hỗ trợ Enter để gửi, Shift+Enter xuống dòng, auto-resize textarea
 */
function ChatInput() {
  const dispatch = useDispatch();
  const isLoading = useSelector(selectIsChatLoading);
  const hybridEnabled = useSelector(selectHybridEnabled);
  const rerankerEnabled = useSelector(selectRerankerEnabled);
  const selfRagEnabled = useSelector(selectSelfRagEnabled);
  const selfRagConfig = useSelector(selectSelfRagConfig);
  const coRagEnabled = useSelector(selectCoRagEnabled);
  const coRagConfig = useSelector(selectCoRagConfig);
  const activeFileFilter = useSelector(selectActiveFileFilter);

  const [input, setInput] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    setInput("");

    // Optimistic update — thêm user message ngay
    dispatch(addUserMessage(trimmed));

    const result = await dispatch(
      sendMessage({
        question: trimmed,
        options: {
          hybridEnabled,
          rerankerEnabled,
          selfRagEnabled,
          selfRagQueryRewrite: selfRagConfig.queryRewrite,
          selfRagRelevanceFilter: selfRagConfig.relevanceFilter,
          selfRagAnswerGrading: selfRagConfig.answerGrading,
          coRagEnabled,
          coRagMergeStrategy: coRagConfig.strategy,
          coRagAgentSemantic: coRagConfig.semantic,
          coRagAgentKeyword: coRagConfig.keyword,
          coRagAgentConceptual: coRagConfig.conceptual,
          activeFileFilter,
        },
      })
    );

    if (sendMessage.rejected.match(result)) {
      toast.error(result.payload || "Gửi tin nhắn thất bại!");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-shrink-0 border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm px-4 py-3">
      <div className="flex gap-2 items-end max-w-full">
        <div className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus-within:border-blue-500 dark:focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all shadow-sm">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            placeholder="Nhập câu hỏi của bạn... (Enter để gửi, Shift+Enter xuống dòng)"
            className="w-full bg-transparent text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 px-4 py-3 resize-none focus:outline-none leading-relaxed disabled:opacity-50"
          />
        </div>

        <Button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="h-10 w-10 p-0 flex-shrink-0 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 shadow-sm shadow-blue-600/30"
          id="chat-send-btn"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-white" />
          ) : (
            <Send className="h-4 w-4 text-white" />
          )}
        </Button>
      </div>
      <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1.5 text-center">
        Enter để gửi · Shift+Enter xuống dòng
      </p>
    </div>
  );
}

export default ChatInput;
