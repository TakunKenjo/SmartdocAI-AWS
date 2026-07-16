import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useDispatch } from "react-redux";
import { useState } from "react";
import { login } from "@/store/slices/authSlice.js";
import { toast } from "sonner";

const LoginForm = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (errors[e.target.name]) setErrors({ ...errors, [e.target.name]: null });
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email.trim()) {
      newErrors.email = "Vui lòng nhập email.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Email không hợp lệ.";
    }
    if (!formData.password) {
      newErrors.password = "Vui lòng nhập mật khẩu.";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await dispatch(login(formData)).unwrap();
      toast.success("Đăng nhập thành công!", {
        description: `Xin chào, ${formData.email.split("@")[0]}!`,
      });
      navigate("/app");
    } catch (error) {
      toast.error("Đăng nhập thất bại", { description: error });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-7">
        <h2 className="text-2xl font-bold text-slate-100 mb-1">Đăng nhập</h2>
        <p className="text-slate-400 text-sm">
          Chưa có tài khoản?{" "}
          <Link
            to="/register"
            className="text-blue-400 font-medium hover:text-blue-300 transition-colors"
          >
            {/* Đăng ký ngay */}
            Đăng ký ngay!
          </Link>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Email */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-300">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className={`pl-9 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500/20 ${
                errors.email ? "border-red-500 focus:border-red-500" : ""
              }`}
              placeholder="you@example.com"
            />
          </div>
          {errors.email && (
            <p className="text-red-400 text-xs flex items-center gap-1">
              <span>⚠</span> {errors.email}
            </p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-300">Mật khẩu</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              name="password"
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={handleChange}
              className={`pl-9 pr-10 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:ring-blue-500/20 ${
                errors.password ? "border-red-500 focus:border-red-500" : ""
              }`}
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-red-400 text-xs flex items-center gap-1">
              <span>⚠</span> {errors.password}
            </p>
          )}
        </div>

        {/* Submit */}
        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold h-10 mt-2 shadow-lg shadow-blue-600/20 transition-all duration-200"
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Đang đăng nhập...
            </span>
          ) : (
            "Đăng nhập"
          )}
        </Button>

        {/* Divider */}
        <div className="relative my-1">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-700" />
          </div>
          <div className="relative flex justify-center">
            <span className="px-3 bg-slate-900 text-xs text-slate-500 font-medium">
              hoặc tiếp tục với
            </span>
          </div>
        </div>

        {/* Google Login Button */}
        <button
          type="button"
          onClick={() =>
            toast.info("Đang phát triển", {
              description: "Đăng nhập bằng Google sẽ sớm được hỗ trợ. Vui lòng dùng email & mật khẩu.",
              duration: 3500,
            })
          }
          className="w-full flex items-center justify-center gap-3 h-10 rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-750 hover:border-slate-600 text-slate-200 text-sm font-medium transition-all duration-200 group relative overflow-hidden"
        >
          {/* Google shimmer effect on hover */}
          <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-transparent via-white/[0.04] to-transparent" />
          {/* Google "G" SVG icon chính thức */}
          <svg viewBox="0 0 24 24" className="h-4 w-4 flex-shrink-0" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
          <span>Đăng nhập bằng Google</span>
        </button>
      </form>
    </div>
  );
};

export default LoginForm;