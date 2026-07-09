import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, Lock, User, Calendar, Phone, Eye, EyeOff } from "lucide-react";
import { useDispatch } from "react-redux";
import { useState } from "react";
import { register } from "@/store/slices/authSlice.js";
import { toast } from "sonner";

const RegisterForm = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({
    fullname: "", email: "", phone: "", dob: "", password: "", confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (errors[e.target.name]) setErrors({ ...errors, [e.target.name]: null });
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.fullname.trim()) newErrors.fullname = "Vui lòng nhập họ tên.";
    if (!formData.email.trim()) {
      newErrors.email = "Vui lòng nhập email.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Email không hợp lệ.";
    }
    if (!formData.phone.trim()) {
      newErrors.phone = "Vui lòng nhập số điện thoại.";
    } else if (!/^[0-9]{9,11}$/.test(formData.phone.replace(/\s/g, ""))) {
      newErrors.phone = "Số điện thoại không hợp lệ.";
    }
    if (!formData.dob) newErrors.dob = "Vui lòng chọn ngày sinh.";
    if (!formData.password) {
      newErrors.password = "Vui lòng nhập mật khẩu.";
    } else if (formData.password.length < 6) {
      newErrors.password = "Mật khẩu phải từ 6 ký tự.";
    }
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Mật khẩu không khớp.";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await dispatch(register(formData)).unwrap();
      toast.success("Đăng ký thành công!", {
        description: "Vui lòng đăng nhập để tiếp tục.",
      });
      navigate("/login");
    } catch (error) {
      toast.error("Lỗi đăng ký", { description: error });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper to render a field error
  const FieldError = ({ field }) =>
    errors[field] ? (
      <p className="text-red-400 text-xs flex items-center gap-1 mt-1">
        <span>⚠</span> {errors[field]}
      </p>
    ) : null;

  const inputClass = (field) =>
    `bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500/20 pl-9 ${
      errors[field] ? "border-red-500 focus:border-red-500" : ""
    }`;

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-100 mb-1">Tạo tài khoản</h2>
        <p className="text-slate-400 text-sm">
          Đã có tài khoản?{" "}
          <Link
            to="/login"
            className="text-blue-400 font-medium hover:text-blue-300 transition-colors"
          >
            Đăng nhập
          </Link>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5" noValidate>
        {/* Họ tên */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Họ và tên</label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              name="fullname"
              value={formData.fullname}
              onChange={handleChange}
              className={inputClass("fullname")}
              placeholder="Nguyễn Văn A"
            />
          </div>
          <FieldError field="fullname" />
        </div>

        {/* Email */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className={inputClass("email")}
              placeholder="you@example.com"
            />
          </div>
          <FieldError field="email" />
        </div>

        {/* Phone + DOB grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-300">Điện thoại</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                className={inputClass("phone")}
                placeholder="0901234567"
              />
            </div>
            <FieldError field="phone" />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-300">Ngày sinh</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                name="dob"
                type="date"
                value={formData.dob}
                onChange={handleChange}
                className={inputClass("dob")}
              />
            </div>
            <FieldError field="dob" />
          </div>
        </div>

        {/* Password */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Mật khẩu</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              name="password"
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={handleChange}
              className={`${inputClass("password")} pr-10`}
              placeholder="Tối thiểu 6 ký tự"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <FieldError field="password" />
        </div>

        {/* Confirm Password */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Xác nhận mật khẩu</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              name="confirmPassword"
              type={showConfirm ? "text" : "password"}
              value={formData.confirmPassword}
              onChange={handleChange}
              className={`${inputClass("confirmPassword")} pr-10`}
              placeholder="Nhập lại mật khẩu"
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <FieldError field="confirmPassword" />
        </div>

        {/* Submit */}
        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold h-10 mt-1 shadow-lg shadow-blue-600/20 transition-all duration-200"
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Đang đăng ký...
            </span>
          ) : (
            "Tạo tài khoản"
          )}
        </Button>
      </form>
    </div>
  );
};

export default RegisterForm;