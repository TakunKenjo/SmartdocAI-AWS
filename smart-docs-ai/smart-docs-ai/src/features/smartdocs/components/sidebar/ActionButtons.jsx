import { useState } from "react";
import { useDispatch } from "react-redux";
import { Trash2, FileX } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { clearDocuments, clearChatHistory } from "@/store/slices/smartdocSlice.js";
import { toast } from "sonner";

/**
 * ActionButtons — Nút xóa lịch sử chat và xóa tài liệu
 * Dùng ShadCN Dialog để confirm trước khi xóa
 */
function ActionButtons() {
  const dispatch = useDispatch();
  const [confirmType, setConfirmType] = useState(null); // 'history' | 'docs'
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      if (confirmType === "history") {
        await dispatch(clearChatHistory()).unwrap();
        toast.success("Đã xóa lịch sử chat!");
      } else {
        await dispatch(clearDocuments()).unwrap();
        toast.success("Đã xóa toàn bộ tài liệu!");
      }
    } catch {
      toast.error("Xóa thất bại, thử lại sau!");
    } finally {
      setLoading(false);
      setConfirmType(null);
    }
  };

  return (
    <>
      <div className="grid grid-cols-2 gap-1.5">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setConfirmType("history")}
          className="text-xs font-semibold hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 hover:border-red-200 dark:hover:border-red-800 transition-all"
        >
          <Trash2 className="h-3.5 w-3.5 mr-1" />
          Xóa lịch sử
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setConfirmType("docs")}
          className="text-xs font-semibold hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 hover:border-red-200 dark:hover:border-red-800 transition-all"
        >
          <FileX className="h-3.5 w-3.5 mr-1" />
          Xóa tài liệu
        </Button>
      </div>

      {/* Confirm Dialog */}
      <Dialog open={!!confirmType} onOpenChange={() => setConfirmType(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <Trash2 className="h-4 w-4" />
              Xác nhận xóa
            </DialogTitle>
            <DialogDescription className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
              {confirmType === "history"
                ? "Bạn có chắc chắn muốn xóa toàn bộ lịch sử chat? Hành động này không thể hoàn tác."
                : "Bạn có chắc chắn muốn xóa toàn bộ tài liệu đã upload và vector store? Hành động này không thể hoàn tác."}
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-2 mt-2">
            <Button
              onClick={handleConfirm}
              disabled={loading}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold"
              size="sm"
            >
              {loading ? "Đang xóa..." : "Xác nhận xóa"}
            </Button>
            <Button
              variant="outline"
              onClick={() => setConfirmType(null)}
              disabled={loading}
              className="flex-1"
              size="sm"
            >
              Hủy bỏ
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default ActionButtons;
