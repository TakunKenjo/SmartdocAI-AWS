import { useSelector } from "react-redux";
import { selectProcessedFiles } from "@/store/slices/smartdocSlice.js";
import FileCard from "./FileCard.jsx";

/**
 * FileList — Danh sách file đã được xử lý (mới nhất lên đầu)
 */
function FileList() {
  const files = useSelector(selectProcessedFiles);

  if (!files.length) {
    return (
      <div className="text-center py-4 text-sm text-slate-400 dark:text-slate-500 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
        Chưa có tài liệu nào được xử lý.
        <br />
        Hãy tải file PDF hoặc DOCX lên ở phía trên.
      </div>
    );
  }

  return (
    <div className="space-y-0.5 max-h-52 overflow-y-auto pr-0.5 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700">
      {[...files].reverse().map((f, i) => (
        <FileCard key={i} file={f} />
      ))}
    </div>
  );
}

export default FileList;
