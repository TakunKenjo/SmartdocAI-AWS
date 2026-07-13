import { useSelector, useDispatch } from "react-redux";
import { selectProcessedFiles, deleteDocument } from "@/store/slices/smartdocSlice.js";
import FileCard from "./FileCard.jsx";
import { toast } from "sonner";

/**
 * FileList — Danh sách file đã được xử lý (mới nhất lên đầu)
 */
function FileList() {
  const dispatch = useDispatch();
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

  const handleDelete = async (filename) => {
    const result = await dispatch(deleteDocument(filename));
    if (deleteDocument.fulfilled.match(result)) {
      toast.success(`Đã xóa tài liệu "${filename}" thành công!`);
    } else {
      toast.error(result.payload || `Lỗi khi xóa tài liệu: ${filename}`);
    }
  };

  return (
    <div className="space-y-0.5 max-h-52 overflow-y-auto pr-0.5 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700">
      {[...files].reverse().map((f, i) => (
        <FileCard 
          key={i} 
          file={f} 
          onRemove={() => handleDelete(f.name)}
        />
      ))}
    </div>
  );
}

export default FileList;
