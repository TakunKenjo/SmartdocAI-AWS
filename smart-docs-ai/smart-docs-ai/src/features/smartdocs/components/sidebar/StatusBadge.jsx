import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

/**
 * StatusBadge — Hiển thị trạng thái kết nối Ollama (online/offline)
 * Theo design SmartdocAI: màu success/error với dot pulse animation
 */
function StatusBadge({ status, loading }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold mb-4 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Đang kiểm tra kết nối...
      </div>
    );
  }

  const isOnline = status?.online;
  const provider = status?.provider || "LLM";
  const model = status?.model || "";

  return (
    <div
      title={
        isOnline
          ? `${provider} đang hoạt động${model ? ` — ${model}` : ""}`
          : `${provider} không khả dụng`
      }
      className={cn(
        "flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold mb-4 border transition-all",
        isOnline
          ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800"
          : "bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800"
      )}
    >
      <span
        className={cn(
          "w-2 h-2 rounded-full flex-shrink-0",
          isOnline
            ? "bg-emerald-500 shadow-[0_0_6px_rgba(34,197,94,0.8)] animate-pulse"
            : "bg-red-500"
        )}
      />
      <span className="truncate">
        {isOnline
          ? `${provider} đang hoạt động${model ? ` — ${model}` : ""}`
          : `${provider} không khả dụng`}
      </span>
    </div>
  );
}

export default StatusBadge;  