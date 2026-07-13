import { useState } from "react";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";

/**
 * SourceCitationPanel — Hiển thị citation badges + expandable source cards
 * Theo design SmartdocAI: badges row + expander chi tiết với score bar
 */
function SourceCitationPanel({ sources, question = "", answer = "" }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources?.length) return null;

  return (
    <div className="w-full border-t border-slate-200 dark:border-slate-700 pt-3 mt-1">
      {/* Citation badges */}
      <div className="flex flex-wrap gap-1.5 mb-2">
        {sources.map((src, idx) => {
          const pageStr = src.total_pages
            ? `Trang ${src.page}/${src.total_pages}`
            : `Trang ${src.page}`;
          return (
            <span
              key={idx}
              className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full px-2.5 py-0.5"
            >
              <FileText className="h-2.5 w-2.5" />
              {src.file} — {pageStr}
            </span>
          );
        })}
      </div>

      {/* Toggle expand */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-[11px] font-semibold text-blue-500 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
      >
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        {expanded ? "Ẩn" : "Xem"} {sources.length} nguồn trích dẫn
      </button>

      {/* Expanded source cards */}
      {expanded && (
        <div className="mt-3 space-y-3">
          {/* Color legend */}
          <div className="flex gap-4 text-[10px] px-2 py-1.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-amber-300/60" />
              <strong>Đoạn được dùng để trả lời</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-blue-200/60" />
              Từ khóa câu hỏi
            </span>
          </div>

          {sources.map((src, idx) => {
            const scorePct = Math.min(100, Math.round((src.score || 0) * 100));
            const isDocx = src.file_type?.toLowerCase() === "docx";
            const pageStr = src.total_pages
              ? `${src.page} / ${src.total_pages}`
              : src.page;

            return (
              <div
                key={idx}
                className="relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden hover:border-blue-300 dark:hover:border-blue-700 transition-all"
              >
                {/* Left accent bar */}
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500 rounded-r" />

                <div className="px-4 py-3">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                        {src.chunk_index || idx + 1}
                      </span>
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[200px]">
                        {isDocx ? "DOCX" : "PDF"} {src.file}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded px-2 py-0.5">
                        Trang {pageStr}
                      </span>
                      <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-0.5 uppercase tracking-wider">
                        {src.file_type || "PDF"}
                      </span>
                    </div>
                  </div>

                  {/* Score bar */}
                  {/* <div className="flex items-center gap-2 mb-2.5">
                    <span className="text-[10px] text-slate-400 dark:text-slate-500 w-16 whitespace-nowrap">
                      Độ liên quan
                    </span>
                    <div className="flex-1 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all duration-500"
                        style={{ width: `${scorePct}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 w-8 text-right">
                      {scorePct}%
                    </span>
                  </div> */}

                  {/* Content */}
                  <div className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 max-h-36 overflow-y-auto font-mono whitespace-pre-wrap break-words">
                    {src.content}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default SourceCitationPanel;
