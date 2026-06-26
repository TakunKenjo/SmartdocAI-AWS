import { FileText, BookOpen, Hash } from "lucide-react";

/**
 * KpiRow — Hiển thị 3 thống kê: số tài liệu, số trang, số chunks
 * Theo design SmartdocAI: 3 box cạnh nhau, accent color, hover effect
 */
function KpiRow({ totalFiles, totalPages, totalChunks }) {
  const items = [
    { label: "Tài liệu", value: totalFiles, icon: FileText },
    { label: "Trang", value: totalPages, icon: BookOpen },
    { label: "Chunks", value: totalChunks, icon: Hash },
  ];

  return (
    <div className="flex gap-1.5 mb-4 flex-wrap">
      {items.map(({ label, value, icon: Icon }) => (
        <div
          key={label}
          className="flex-1 min-w-[70px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 text-center hover:border-blue-300 dark:hover:border-blue-700 transition-all group"
        >
          <Icon className="h-3.5 w-3.5 text-blue-500 mx-auto mb-1 opacity-70 group-hover:opacity-100 transition-opacity" />
          <div className="text-lg font-bold text-blue-600 dark:text-blue-400 leading-none">
            {value}
          </div>
          <div className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mt-1 font-medium">
            {label}
          </div>
        </div>
      ))}
    </div>
  );
}

export default KpiRow;
