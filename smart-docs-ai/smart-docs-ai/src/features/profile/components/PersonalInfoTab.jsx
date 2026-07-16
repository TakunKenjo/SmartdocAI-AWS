import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";
import { useSelector, useDispatch } from "react-redux";
import { selectCurrentUser, getProfile } from "@/store/slices/authSlice";
import React, { useState, useEffect } from "react";
import { updatePersonalInfo } from "@/store/slices/authSlice";
import { toast } from "sonner";

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

const PersonalInfoTab = () => {
  const dispatch = useDispatch();
  const user = useSelector(selectCurrentUser);

  const [fullname, setFullname] = useState("");
  const [email,    setEmail]    = useState("");
  const [phone,    setPhone]    = useState("");
  const [dob,      setDob]      = useState("");

  const [errors,      setErrors]      = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load profile từ DynamoDB khi component mount
  useEffect(() => {
    if (user?.id) {
      dispatch(getProfile());
    }
  }, [dispatch, user?.id]);

  // Update form fields khi user thay đổi
  useEffect(() => {
    setFullname(user?.fullname || "");
    setEmail(user?.email || "");
    setPhone(user?.phone || "");
    setDob(user?.dob || "");
  }, [user]);

  const validateForm = () => {
    const newErrors = {};
    if (!fullname.trim())
      newErrors.fullname = "Vui lòng nhập họ tên.";
    if (!email.trim())
      newErrors.email = "Vui lòng nhập email.";
    else if (!/^\S+@\S+\.\S+$/.test(email))
      newErrors.email = "Email không hợp lệ.";
    if (!phone.trim())
      newErrors.phone = "Vui lòng nhập số điện thoại.";
    if (!dob)
      newErrors.dob = "Vui lòng chọn ngày sinh.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleUpdatePersonalInfo = async () => {
    if (!validateForm()) return;
    setIsSubmitting(true);
    try {
      await dispatch(updatePersonalInfo({ fullname, email, phone, dob })).unwrap();
      toast.success("Cập nhật thành công!");
    } catch (error) {
      toast.error("Lỗi!", { description: error });
    } finally {
      setIsSubmitting(false);
    }
  };

  const FieldError = ({ field }) =>
    errors[field] ? (
      <p className="text-red-400 text-[11px] mt-1 flex items-center gap-1">
        <span>⚠</span> {errors[field]}
      </p>
    ) : null;

  return (
    <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
        <p className="text-sm font-bold text-slate-800 dark:text-slate-100">Thông tin cá nhân</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
          Cập nhật thông tin hiển thị của tài khoản bạn
        </p>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        <div className="grid md:grid-cols-2 gap-4">

          {/* Họ tên */}
          <div>
            <label className={labelClass}>Họ và tên</label>
            <Input
              value={fullname}
              onChange={(e) => { setFullname(e.target.value); if (errors.fullname) setErrors({ ...errors, fullname: null }); }}
              className={inputClass(errors.fullname)}
              placeholder="Nguyễn Văn A"
            />
            <FieldError field="fullname" />
          </div>

          {/* Email */}
          <div>
            <label className={labelClass}>Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); if (errors.email) setErrors({ ...errors, email: null }); }}
              className={inputClass(errors.email)}
              placeholder="you@example.com"
            />
            <FieldError field="email" />
          </div>

          {/* Số điện thoại */}
          <div>
            <label className={labelClass}>Số điện thoại</label>
            <Input
              type="tel"
              value={phone}
              onChange={(e) => { setPhone(e.target.value); if (errors.phone) setErrors({ ...errors, phone: null }); }}
              className={inputClass(errors.phone)}
              placeholder="0901234567"
            />
            <FieldError field="phone" />
          </div>

          {/* Ngày sinh */}
          <div>
            <label className={labelClass}>Ngày sinh</label>
            <Input
              type="date"
              value={dob}
              onChange={(e) => { setDob(e.target.value); if (errors.dob) setErrors({ ...errors, dob: null }); }}
              className={inputClass(errors.dob)}
            />
            <FieldError field="dob" />
          </div>

        </div>

        <div className="pt-1">
          <Button
            onClick={handleUpdatePersonalInfo}
            disabled={isSubmitting}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm h-9 px-5 shadow-sm shadow-blue-600/20 transition-all"
          >
            <Save className="h-3.5 w-3.5 mr-1.5" />
            {isSubmitting ? "Đang lưu..." : "Lưu thay đổi"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default PersonalInfoTab;