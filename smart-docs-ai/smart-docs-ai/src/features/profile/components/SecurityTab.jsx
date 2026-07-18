import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useSelector } from "react-redux";
import React, { useState, useCallback, memo } from "react";
import { useDispatch } from "react-redux";
import { toast } from "sonner";
import { changePassword } from "@/store/slices/authSlice";
import { Save, Eye, EyeOff } from "lucide-react";

// ── Class dùng chung cho toàn bộ app ─────────────────────────────────────────
const inputClass = (hasError) =>
  [
    "mt-1 w-full rounded-lg border text-sm",
    "bg-white dark:bg-slate-900",
    "text-slate-800 dark:text-slate-200",
    "placeholder:text-slate-400 dark:placeholder:text-slate-500",
    "focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 dark:focus:ring-blue-400/30 dark:focus:border-blue-400",
    "transition-all",
    hasError
      ? "border-red-400 dark:border-red-500"
      : "border-slate-200 dark:border-slate-700",
  ].join(" ");

const labelClass =
  "text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1";

// ── PasswordField Component (memoized để tránh re-render) ──
const FieldError = memo(({ field, error }) =>
  error ? (
    <p className="text-red-400 text-[11px] mt-1 flex items-center gap-1">
      <span>⚠</span> {error}
    </p>
  ) : null
);

const PasswordField = memo(({ label, value, onChange, show, onToggle, field, error, placeholder }) => (
  <div>
    <label className={labelClass}>{label}</label>
    <div className="relative mt-1">
      <Input
        type={show ? "text" : "password"}
        value={value}
        onChange={onChange}
        autoComplete="off"
        spellCheck="false"
        className={[inputClass(!!error), "pr-10"].join(" ")}
        placeholder={placeholder}
      />
      <button
        type="button"
        onClick={onToggle}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
      >
        {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
    <FieldError field={field} error={error} />
  </div>
));

const SecurityTab = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const isGoogleUser =
    user?.authProvider === "google" || user?.cognitoUsername?.startsWith("Google_");

  const [currentPassword,  setCurrentPassword]  = useState("");
  const [newPassword,      setNewPassword]       = useState("");
  const [confirmPassword,  setConfirmPassword]   = useState("");

  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew,     setShowNew]     = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [errors,       setErrors]       = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCurrentPasswordChange = useCallback((e) => {
    setCurrentPassword(e.target.value);
    setErrors((prev) => ({ ...prev, currentPassword: null }));
  }, []);

  const handleNewPasswordChange = useCallback((e) => {
    setNewPassword(e.target.value);
    setErrors((prev) => ({ ...prev, newPassword: null }));
  }, []);

  const handleConfirmPasswordChange = useCallback((e) => {
    setConfirmPassword(e.target.value);
    setErrors((prev) => ({ ...prev, confirmPassword: null }));
  }, []);

  const handleToggleShowCurrent = useCallback(() => {
    setShowCurrent((prev) => !prev);
  }, []);

  const handleToggleShowNew = useCallback(() => {
    setShowNew((prev) => !prev);
  }, []);

  const handleToggleShowConfirm = useCallback(() => {
    setShowConfirm((prev) => !prev);
  }, []);

  const validateForm = () => {
    const newErrors = {};
    if (!isGoogleUser && !currentPassword)
      newErrors.currentPassword = "Vui lòng nhập mật khẩu hiện tại.";
    if (!newPassword)
      newErrors.newPassword = "Vui lòng nhập mật khẩu mới.";
    else if (newPassword.length < 6)
      newErrors.newPassword = "Mật khẩu phải có ít nhất 6 ký tự.";
    if (!confirmPassword)
      newErrors.confirmPassword = "Vui lòng xác nhận mật khẩu.";
    else if (confirmPassword !== newPassword)
      newErrors.confirmPassword = "Mật khẩu xác nhận không khớp.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChangePassword = async () => {
    if (!validateForm()) return;
    setIsSubmitting(true);
    try {
      await dispatch(changePassword({ currentPassword, newPassword, isGoogleUser })).unwrap();
      toast.success(isGoogleUser ? "Thiết lập mật khẩu thành công!" : "Đổi mật khẩu thành công!");
      setCurrentPassword(""); setNewPassword(""); setConfirmPassword("");
    } catch (error) {
      toast.error("Đã xảy ra lỗi!", { description: error });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
        <p className="text-sm font-bold text-slate-800 dark:text-slate-100">Bảo mật</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
          {isGoogleUser
            ? "Thiết lập mật khẩu để có thể đăng nhập bằng email và mật khẩu"
            : "Thay đổi mật khẩu đăng nhập của bạn"}
        </p>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">

        {!isGoogleUser && (
          <PasswordField
            label="Mật khẩu hiện tại"
            value={currentPassword}
            onChange={handleCurrentPasswordChange}
            show={showCurrent}
            onToggle={handleToggleShowCurrent}
            error={errors.currentPassword}
            placeholder="••••••••"
          />
        )}

        <PasswordField
          label="Mật khẩu mới"
          value={newPassword}
          onChange={handleNewPasswordChange}
          show={showNew}
          onToggle={handleToggleShowNew}
          error={errors.newPassword}
          placeholder="Tối thiểu 6 ký tự"
        />

        <PasswordField
          label="Xác nhận mật khẩu mới"
          value={confirmPassword}
          onChange={handleConfirmPasswordChange}
          show={showConfirm}
          onToggle={handleToggleShowConfirm}
          error={errors.confirmPassword}
          placeholder="Nhập lại mật khẩu mới"
        />

        {/* Info note */}
        <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed">
          {isGoogleUser
            ? "Sau khi thiết lập, bạn vẫn có thể đăng nhập bằng Google hoặc dùng email và mật khẩu mới."
            : "Mật khẩu mới sẽ được áp dụng cho tất cả thiết bị đăng nhập tiếp theo."}
        </p>

        <div className="pt-1">
          <Button
            onClick={handleChangePassword}
            disabled={isSubmitting}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm h-9 px-5 shadow-sm shadow-blue-600/20 transition-all"
          >
            <Save className="h-3.5 w-3.5 mr-1.5" />
            {isSubmitting
              ? "Đang cập nhật..."
              : isGoogleUser
                ? "Thiết lập mật khẩu"
                : "Cập nhật mật khẩu"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SecurityTab;