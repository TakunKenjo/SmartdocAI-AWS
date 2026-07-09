import {Link, useNavigate} from "react-router"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from "@/components/ui/card"

import { Input } from "@/components/ui/input"
import { Mail, Lock } from "lucide-react"
import {useDispatch} from "react-redux";
import {useState} from "react";
import {login} from "@/store/slices/authSlice.js";
import {toast} from "sonner";

const LoginForm = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (errors[e.target.name]) setErrors({ ...errors, [e.target.name]: null });
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email.trim()) {
      newErrors.email = "Vui lòng nhập email.";
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
      toast.success("Đăng nhập thành công!");
      navigate("/"); // Chuyển hướng vào Dashboard
    } catch (error) {
      toast.error("Đăng nhập thất bại", { description: error });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full border-none shadow-none">

      <CardHeader>
        <CardTitle className="text-2xl text-center">Đăng nhập</CardTitle>
        <CardDescription className="text-center">
          Bạn chưa có tài khoản? 
          <Link
            to="/register"
            className="text-emerald-600 cursor-pointer ml-1 font-medium hover:underline"
          >
            Đăng ký
          </Link>
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {/* Email */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`pl-9 ${errors.email ? "border-rose-500" : ""}`}
                  placeholder="Nhập email của bạn" />
            </div>
            {errors.email && <p className="text-rose-500 text-xs">{errors.email}</p>}
          </div>

          {/* Mật khẩu */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Mật khẩu</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`pl-9 ${errors.password ? "border-rose-500" : ""}`}
                  placeholder="Nhập mật khẩu" />
            </div>
            {errors.password && <p className="text-rose-500 text-xs">{errors.password}</p>}
          </div>

          <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 mt-4 text-white dark:bg-emerald-700 dark:hover:bg-emerald-800"
          >
            {isSubmitting ? "Đang xử lý..." : "Đăng nhập"}
          </Button>
        </form>
      </CardContent>

    </Card>
  )
}

export default LoginForm