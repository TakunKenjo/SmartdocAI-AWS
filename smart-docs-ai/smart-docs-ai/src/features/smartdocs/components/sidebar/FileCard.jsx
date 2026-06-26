import { cn } from "@/lib/utils";

/**
 * FileCard — Hiển thị một file item với icon, tên, size, badge chunks
 * Theo design SmartdocAI: compact card với PDF/DOCX icon, hover effect
 */
function FileCard({ file, badge, badgeText }) {
  const name = file?.name || "";
  const isDocx = name.toLowerCase().endsWith(".docx");
  const fileType = isDocx ? "DOCX" : "PDF";

  // Format size nếu có
  const sizeStr = file?.size
    ? file.size < 1024 * 1024
      ? `${(file.size / 1024).toFixed(0)} KB`
      : `${(file.size / (1024 * 1024)).toFixed(1)} MB`
    : file?.pages
      ? `${file.pages} trang`
      : "";

  return (
    <div className="flex items-center gap-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2.5 mb-1.5 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600 transition-all group">
      {/* File icon */}
      <div
        className={cn(
          "w-8 h-8 rounded-md flex items-center justify-center text-[10px] font-bold flex-shrink-0",
          isDocx
            ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
            : "bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400"
        )}
      >
        {fileType}
      </div>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate leading-tight">
          {name}
        </p>
        {sizeStr && (
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{sizeStr}</p>
        )}
      </div>

      {/* Badge */}
      {(badge || badgeText || file?.chunks) && (
        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full px-2 py-0.5 whitespace-nowrap flex-shrink-0">
          {badgeText || `${file?.chunks} chunks`}
        </span>
      )}
    </div>
  );
}

export default FileCard;
