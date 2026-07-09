import LoginForm from "../components/LoginForm"
import {useNavigate} from "react-router";

const LoginPage = () => {
  const navigate = useNavigate();

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-100 via-white to-emerald-200 p-6 dark:from-slate-700 dark:via-slate-900 dark:to-slate-900">
      
      <div className="w-full max-w-5xl bg-white rounded-2xl shadow-xl overflow-hidden grid grid-cols-1 md:grid-cols-2">

        {/* Bên trái */}
        <div className="hidden md:flex flex-col justify-center items-center bg-gradient-to-br from-emerald-400 to-emerald-600 text-white p-10 dark:bg-gradient-to-br dark:from-emerald-600 to-emerald-700">
          
          <h2 className="text-3xl font-bold mb-4 text-center">
            Chào mừng đến với ứng dụng!
          </h2>

          <p className="text-center text-sm opacity-90">
            Quản lý thu chi cá nhân dễ dàng, theo dõi tài chính của bạn mọi lúc mọi nơi.
          </p>

          <div className="flex gap-3 mt-6">
            <div className="w-3 h-3 bg-white/70 rounded-full"></div>
            <div title="Trang Đăng ký" onClick={() => navigate("/register")} className="cursor-pointer w-3 h-3 bg-white/40 rounded-full"></div>
          </div>

        </div>

        {/* Bên phải */}
        <div className="p-10 flex items-center dark:bg-slate-950">
          <LoginForm />
        </div>

      </div>

    </main>
  )
}

export default LoginPage