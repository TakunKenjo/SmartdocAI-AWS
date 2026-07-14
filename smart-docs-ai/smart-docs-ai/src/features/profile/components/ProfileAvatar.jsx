import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Camera, Upload, X, Check, ImageIcon } from "lucide-react"

import { useSelector, useDispatch } from "react-redux";
import { useState, useRef, useCallback } from "react";
import { toast } from "sonner";
import { updateAvatar } from "@/store/slices/authSlice";

// Hàm nén ảnh -> kiểu giảm kích thước ảnh lại chứ lớn quá là lỗi, ko convert lưu Base64 được
const resizeImage = (file, maxWidth = 300, quality = 0.7) =>
  new Promise((resolve, reject) => {
    const img = new Image();
    const reader = new FileReader(); // đọc ảnh và convert Base64 tạm

    reader.onload = (e) => {
      img.src = e.target.result;
    };

    img.onload = () => {
      const canvas = document.createElement("canvas");
      const scale = maxWidth / img.width;

      canvas.width = maxWidth;
      canvas.height = img.height * scale;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // trả về Bloc - Ảnh đã nén (nhưng chưa là base64)
      canvas.toBlob(
        (blob) => {
          if (!blob) return reject(new Error("Resize thất bại!"));
          resolve(blob);
        },
        "image/jpeg",
        quality
      );
    };

    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

// Hàm biến file thành chuỗi base64
const fileToBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result); // "data:image/png;base64,..."
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

// Initial khi chưa có avatar, ví dụ Ngô Đức Trọng -> NĐ
const getInitials = (fullname = "") =>
  fullname
    .trim()
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U";


const ProfileAvatar = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);

  const [previewUrl, setPreviewUrl] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef(null);

  // Chọn ảnh 
  const handleFile = useCallback((file) => {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Chỉ chấp nhận file ảnh (JPG, PNG, GIF, WEBP)!");
      return;
    }

    // Giới hạn 5MB
    if (file.size > 5 * 1024 * 1024) {
        toast.error("Ảnh phải nhỏ hơn 5MB!");
        return;
    }

    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });

    setSelectedFile(file);
  }, []);

  const handleFileInputChange = (e) => {
    handleFile(e.target.files?.[0]);
    e.target.value = "";
  };

  // Drag Ảnh vào 
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  // Drop ảnh -> Gọi lại logic chọn File
  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      handleFile(e.dataTransfer.files?.[0]);
    },
    [handleFile]
  );

  // Hủy chọn ảnh
  const handleCancel = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setSelectedFile(null);
  };

  // Save button
  const handleSave = async () => {
    if (!selectedFile) return;
    setIsSubmitting(true);
    try {
      const resizedBlob = await resizeImage(selectedFile, 300, 0.7);

      // convert lại sang file
      const resizedFile = new File([resizedBlob], selectedFile.name, {
      type: "image/jpeg",
      });

      // convert base64
      const base64 = await fileToBase64(resizedFile);
      console.log("Sau resize:", (resizedFile.size / 1024).toFixed(0), "KB");    
      await dispatch(updateAvatar({ avatar: base64 })).unwrap();
      toast.success("Cập nhật ảnh đại diện thành công!");
      setSelectedFile(null);
    } catch (error) {
      toast.error("Lỗi khi cập nhật ảnh!", { description: String(error) });
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentAvatar = previewUrl || user?.avatar || null;

  return (
    <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm p-5 flex flex-col items-center gap-5 transition-all duration-300 hover:shadow-md">

      <div className="text-center space-y-0.5">
        <p className="text-sm font-bold text-slate-800 dark:text-slate-100">Ảnh đại diện</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500">
          Kéo thả hoặc click để cập nhật
        </p>
      </div>

      {/* Vùng Drag & Drop */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isSubmitting && fileInputRef.current?.click()}
        className={[
          "w-full flex flex-col items-center gap-3 py-5 px-4 rounded-xl",
          "border-2 border-dashed cursor-pointer select-none",
          "transition-all duration-200",
          isDragging
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-[1.02]"
            : "border-slate-200 dark:border-slate-700 hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-900/10",
          isSubmitting ? "pointer-events-none opacity-70" : "",
        ].join(" ")}
      >
        {/* Avatar */}
        <div className="relative w-28 h-28 group shrink-0">
          {currentAvatar ? (
            <img
              src={currentAvatar}
              alt="Avatar"
              className="w-28 h-28 rounded-full object-cover ring-4 ring-white dark:ring-gray-800 shadow-md"
            />
          ) : (
            <div className="w-28 h-28 rounded-full bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center text-2xl font-bold text-white shadow-md ring-4 ring-white dark:ring-slate-800">
              {getInitials(user?.fullname)}
            </div>
          )}
          <div className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <Camera className="h-7 w-7 text-white" />
          </div>
        </div>
        {/* Description về File */}
        <div className="text-center pointer-events-none space-y-0.5">
          {isDragging ? (
            <p className="text-xs font-semibold text-blue-600 dark:text-blue-400">
              Thả ảnh vào đây!
            </p>
          ) : (
            <>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                <span className="font-semibold text-blue-600 dark:text-blue-400">
                  Kéo & thả
                </span>{" "}
                ảnh vào đây
              </p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">
                hoặc click để chọn • JPG, PNG, WEBP • tối đa 5MB
              </p>
            </>
          )}
        </div>
      </div>

      {/* Input file ẩn */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Tên file đã chọn */}
      {selectedFile && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground -mt-2 max-w-full px-1">
          <ImageIcon className="h-3.5 w-3.5 shrink-0 text-blue-500" />
          <span className="truncate text-slate-600 dark:text-slate-300">{selectedFile.name}</span>
          <span className="shrink-0 text-slate-400 dark:text-slate-500">
            ({(selectedFile.size / 1024).toFixed(0)} KB)
          </span>
        </div>
      )}

       {/* Button */}
      <div className="w-full flex gap-2">
        {selectedFile ? (
          <>
            <Button
              variant="outline"
              className="flex-1"
              disabled={isSubmitting}
              onClick={(e) => { e.stopPropagation(); handleCancel(); }}
            >
              <X className="h-4 w-4 mr-1.5" />
              Hủy
            </Button>
            <Button
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white shadow-sm shadow-blue-600/30"
              disabled={isSubmitting}
              onClick={(e) => { e.stopPropagation(); handleSave(); }}
            >
              {isSubmitting ? (
                <>
                  <Upload className="h-4 w-4 mr-1.5 animate-bounce" />
                  Đang lưu...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-1.5" />
                  Lưu ảnh
                </>
              )}
            </Button>
          </>
        ) : (
          <Button
            variant="outline"
            className="w-full"
            onClick={() => fileInputRef.current?.click()}
          >
            <Camera className="h-4 w-4 mr-2" />
            Đổi ảnh
          </Button>
        )}
      </div>


    </Card>
  )
}

export default ProfileAvatar