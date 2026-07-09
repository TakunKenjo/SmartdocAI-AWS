import { useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Upload, Loader2, CheckCircle2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  uploadDocuments,
  selectIsProcessing,
  selectChunkSize,
  selectChunkOverlap,
} from "@/store/slices/smartdocSlice.js";
import FileCard from "./FileCard.jsx";
import { toast } from "sonner";

/**
 * FileUploader — Drag & drop area để upload PDF/DOCX
 * Theo design SmartdocAI: dashed border, hover highlight, file preview cards
 */
function FileUploader() {
  const dispatch = useDispatch();
  const isProcessing = useSelector(selectIsProcessing);
  const chunkSize = useSelector(selectChunkSize);
  const chunkOverlap = useSelector(selectChunkOverlap);

  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFiles = (fileList) => {
    const valid = Array.from(fileList).filter((f) =>
      f.name.match(/\.(pdf|docx)$/i)
    );
    if (valid.length === 0) {
      toast.error("Chỉ hỗ trợ file PDF và DOCX!");
      return;
    }
    setSelectedFiles(valid);
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleProcess = async () => {
    if (!selectedFiles.length) return;
    const result = await dispatch(
      uploadDocuments({ files: selectedFiles, chunkSize, chunkOverlap })
    );
    if (uploadDocuments.fulfilled.match(result)) {
      toast.success(
        `Đã xử lý ${selectedFiles.length} tài liệu thành công!`
      );
      setSelectedFiles([]);
    } else {
      toast.error(result.payload || "Xử lý thất bại!");
    }
  };

  return (
    <div className="space-y-2">
      {/* Drop zone */}
      <div
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-4 text-center transition-all cursor-pointer
          ${dragOver
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-600 hover:bg-blue-50/50 dark:hover:bg-blue-900/10"
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <Upload className="h-6 w-6 text-blue-400 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
          Kéo-thả hoặc <span className="text-blue-500 dark:text-blue-400 font-semibold">nhấn để chọn</span>
        </p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
          Hỗ trợ PDF và DOCX
        </p>
      </div>

      {/* Selected files preview */}
      {selectedFiles.length > 0 && (
        <div className="space-y-1">
          {selectedFiles.map((f, i) => (
          <FileCard
            key={i}
            file={f}
            badgeText="Sẵn sàng"
            onRemove={() => removeFile(i)}
          />
        ))}
        </div>
      )}

      {/* Process button */}
      {selectedFiles.length > 0 && (
        <Button
          onClick={handleProcess}
          disabled={isProcessing}
          className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white font-semibold"
          size="sm"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Đang xử lý...
            </>
          ) : (
            <>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Xử lý tài liệu
            </>
          )}
        </Button>
      )}
    </div>
  );
}

export default FileUploader;
