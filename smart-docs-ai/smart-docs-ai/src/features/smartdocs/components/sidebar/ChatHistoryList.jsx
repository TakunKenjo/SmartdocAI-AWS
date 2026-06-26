import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { MessageSquare, ChevronRight } from "lucide-react";
import { selectChatHistory } from "@/store/slices/smartdocSlice.js";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

/**
 * ChatHistoryList — Sidebar list các câu hỏi đã hỏi
 * Click vào item mở dialog xem chi tiết Q&A
 */
function ChatHistoryList() {
  const chatHistory = useSelector(selectChatHistory);
  const [selectedPair, setSelectedPair] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Lấy các cặp Q&A từ history
  const qaPairs = [];
  for (let i = 0; i < chatHistory.length; i++) {
    if (chatHistory[i].role === "user") {
      const answer = chatHistory[i + 1]?.role === "assistant" ? chatHistory[i + 1] : null;
      qaPairs.push({ question: chatHistory[i].content, answer });
      if (answer) i++;
    }
  }

  if (!qaPairs.length) {
    return (
      <div className="text-center py-4 text-sm text-slate-400 dark:text-slate-500 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
        Chưa có cuộc hội thoại nào.
        <br />
        Hãy đặt câu hỏi để bắt đầu.
      </div>
    );
  }

  return (
    <>
      <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-2">
        {qaPairs.length} câu hỏi — nhấn để xem chi tiết
      </p>

      <div className="space-y-1.5 max-h-64 overflow-y-auto pr-0.5">
        {[...qaPairs].reverse().map((pair, i) => {
          const shortQ = pair.question.slice(0, 60) + (pair.question.length > 60 ? "…" : "");
          const shortA = pair.answer?.content?.slice(0, 80) + (pair.answer?.content?.length > 80 ? "…" : "") || "";

          return (
            <button
              key={i}
              onClick={() => { setSelectedPair(pair); setDialogOpen(true); }}
              className="w-full text-left bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2.5 hover:bg-blue-50/60 dark:hover:bg-blue-900/20 hover:border-blue-200 dark:hover:border-blue-800 transition-all group"
            >
              <div className="flex items-start gap-2">
                <MessageSquare className="h-3.5 w-3.5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 line-clamp-2 leading-snug">
                    {shortQ}
                  </p>
                  {shortA && (
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 line-clamp-2 leading-snug">
                      {shortA}
                    </p>
                  )}
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </button>
          );
        })}
      </div>

      {/* Detail Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="h-4 w-4 text-blue-500" />
              Chi tiết câu hỏi
            </DialogTitle>
          </DialogHeader>

          {selectedPair && (
            <div className="space-y-4">
              {/* Question */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                <p className="text-[11px] font-bold text-blue-500 uppercase tracking-wider mb-2">
                  Người dùng
                </p>
                <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                  {selectedPair.question}
                </p>
              </div>

              {/* Answer */}
              {selectedPair.answer && (
                <div className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                  <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Trợ lý AI
                  </p>
                  <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {selectedPair.answer.content}
                  </p>
                </div>
              )}

              {/* Sources */}
              {selectedPair.answer?.sources?.length > 0 && (
                <div>
                  <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Nguồn tham khảo
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedPair.answer.sources.map((src, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full px-2.5 py-1"
                      >
                        📎 {src.file} — Trang {src.page}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={() => setDialogOpen(false)}
                className="w-full"
              >
                Đóng
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

export default ChatHistoryList;
