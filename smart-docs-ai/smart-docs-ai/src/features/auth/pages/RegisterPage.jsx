import RegisterForm from "../components/RegisterForm";
import { useNavigate } from "react-router";
import { BrainCircuit, Shield, Zap, Users } from "lucide-react";

const RegisterPage = () => {
  const navigate = useNavigate();

  return (
    <div className="auth-page min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-slate-950">

      {/* ── Animated background blobs ── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-indigo-600/20 blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] rounded-full bg-blue-500/15 blur-3xl animate-pulse delay-700" />
        <div className="absolute top-1/3 right-1/3 w-[300px] h-[300px] rounded-full bg-cyan-500/10 blur-3xl" />
      </div>

      {/* ── Subtle grid overlay ── */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* ── Main card ── */}
      <div className="relative z-10 w-full max-w-4xl mx-4 my-8 rounded-2xl overflow-hidden shadow-2xl shadow-black/50 grid grid-cols-1 md:grid-cols-2 border border-white/10">

        {/* ── Left panel — Branding ── */}
        <div className="hidden md:flex flex-col justify-between p-10 bg-gradient-to-br from-indigo-600 via-blue-700 to-blue-800">

          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/15 flex items-center justify-center backdrop-blur-sm border border-white/20">
              <BrainCircuit className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg leading-none">SmartDocAI</h1>
            </div>
          </div>

          {/* Center content */}
          <div className="flex-1 flex flex-col justify-center py-8">
            <h2 className="text-3xl font-bold text-white mb-3 leading-snug">
              Bắt đầu hành trình<br />cùng SmartDocAI
            </h2>
            <p className="text-blue-100/80 text-sm leading-relaxed mb-8">
              Đăng ký miễn phí để trải nghiệm nền tảng phân tích tài liệu AI hàng đầu, được vận hành trên hạ tầng AWS đáng tin cậy.
            </p>

            {/* Benefit pills */}
            <div className="flex flex-col gap-2.5">
              {[
                { icon: Zap, label: "Xử lý tài liệu song song, cực nhanh" },
                { icon: Shield, label: "Dữ liệu được bảo vệ trên Amazon S3" },
                { icon: Users, label: "Miễn phí" },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-2.5 text-blue-100/90 text-sm">
                  <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                    <Icon className="h-3.5 w-3.5 text-blue-200" />
                  </div>
                  {label}
                </div>
              ))}
            </div>
          </div>

          {/* Nav dots */}
          <div className="flex gap-2 items-center">
            <div
              title="Trang Đăng nhập"
              onClick={() => navigate("/login")}
              className="cursor-pointer w-2.5 h-2.5 rounded-full bg-white/30 hover:bg-white/60 transition-colors"
            />
            <div className="w-2.5 h-2.5 rounded-full bg-white/80" />
          </div>
        </div>

        {/* ── Right panel — Form ── */}
        <div className="flex items-center justify-center p-8 bg-slate-900">
          <div className="w-full max-w-sm">

            {/* Mobile logo */}
            <div className="flex md:hidden items-center gap-2.5 mb-6">
              <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/30">
                <BrainCircuit className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-slate-100 text-lg">SmartDocAI</span>
            </div>

            <RegisterForm />
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;