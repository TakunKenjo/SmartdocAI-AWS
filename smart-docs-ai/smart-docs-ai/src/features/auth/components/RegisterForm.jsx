import {Link, useNavigate} from "react-router"
import {Button} from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription
} from "@/components/ui/card"

import {Input} from "@/components/ui/input"
import {Mail, Lock, User, Calendar, BookUser} from "lucide-react"
import {useDispatch} from "react-redux";
import {useState} from "react";
import {register} from "@/store/slices/authSlice.js";
import {toast} from "sonner";

const RegisterForm = () => {
    const navigate = useNavigate();
    const dispatch = useDispatch();

    const [formData, setFormData] = useState({
        fullname: "", email: "", phone: "", dob: "", password: "", confirmPassword: ""
    });
    const [errors, setErrors] = useState({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        if (errors[e.target.name]) setErrors({...errors, [e.target.name]: null});
    };

    const validateForm = () => {
        const newErrors = {};
        if (!formData.fullname.trim()) {
            newErrors.fullname = "Vui lòng nhập họ tên.";
        }
        if (!formData.email.trim()) {
            newErrors.email = "Vui lòng nhập email.";
        } else if (!/^\S+@\S+\.\S+$/.test(formData.email)) {
            newErrors.email = "Email không hợp lệ.";
        }
        if (!formData.phone.trim()) {
            newErrors.phone = "Vui lòng nhập số điện thoại.";
        }
        if (!formData.dob) {
            newErrors.dob = "Vui lòng chọn ngày sinh.";
        }
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
            toast.success("Đăng ký thành công!",
                {description: "Vui lòng đăng nhập để tiếp tục."}
            );
            navigate("/login"); // Chuyển về trang đăng nhập
        } catch (error) {
            toast.error("Lỗi đăng ký", {description: error});
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Card className="w-full border-none shadow-none">
            <CardHeader>
                <CardTitle className="text-2xl text-center">
                    Đăng ký
                </CardTitle>
                <CardDescription className="text-center">
                    Bạn đã có tài khoản?
                    <Link
                        to="/login"
                        className="text-emerald-600 cursor-pointer ml-1 font-medium hover:underline">
                        Đăng nhập
                    </Link>
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-3" noValidate>
                    {/* Họ tên */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium">Họ và tên</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                name="fullname"
                                value={formData.fullname}
                                onChange={handleChange}
                                className={`pl-9 ${errors.fullname ? "border-rose-500" : ""}`}
                                placeholder="Nhập họ tên của bạn" />
                        </div>
                        {errors.fullname && <p className="text-rose-500 text-xs">{errors.fullname}</p>}
                    </div>

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

                    {/* Phone */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium">Số điện thoại</label>
                        <div className="relative">
                            <BookUser className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                name="phone"
                                type="tel"
                                value={formData.phone}
                                onChange={handleChange}
                                className={`pl-9 ${errors.phone ? "border-rose-500" : ""}`}
                                placeholder="Nhập số điện thoại của bạn" />
                        </div>
                        {errors.phone && <p className="text-rose-500 text-xs">{errors.phone}</p>}
                    </div>

                    {/* Ngày sinh */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium">Ngày sinh</label>
                        <div className="relative">
                            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                name="dob"
                                type="date"
                                value={formData.dob}
                                onChange={handleChange}
                                className={`pl-9 ${errors.dob ? "border-rose-500" : ""}`} />
                        </div>
                        {errors.dob && <p className="text-rose-500 text-xs">{errors.dob}</p>}
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

                    {/* Xác nhận mật khẩu */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium">Xác nhận mật khẩu</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                name="confirmPassword"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                className={`pl-9 ${errors.confirmPassword ? "border-rose-500" : ""}`}
                                placeholder="Nhập lại mật khẩu" />
                        </div>
                        {errors.confirmPassword &&
                            <p className="text-rose-500 text-xs">{errors.confirmPassword}</p>
                        }
                    </div>

                    {/* Nút đăng ký */}
                    <Button type="submit"
                            disabled={isSubmitting}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 mt-4 text-white dark:bg-emerald-700 dark:hover:bg-emerald-800">
                        {isSubmitting ? "Đang xử lý..." : "Đăng ký"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    )
}

export default RegisterForm