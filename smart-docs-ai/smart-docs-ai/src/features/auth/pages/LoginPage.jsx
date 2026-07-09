import LoginForm from "../components/LoginForm";
import { useNavigate } from "react-router";
import { BrainCircuit, Sparkles, FileText, MessageSquare } from "lucide-react";

const LoginPage = () => {
  const navigate = useNavigate();

  return (
    <div className="auth-page min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-slate-950">

      {/* ── Animated background blobs ── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-blue-600/20 blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full bg-cyan-500/15 blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-indigo-600/10 blur-3xl" />
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
      <div className="relative z-10 w-full max-w-4xl mx-4 rounded-2xl overflow-hidden shadow-2xl shadow-black/50 grid grid-cols-1 md:grid-cols-2 border border-white/10">

        {/* ── Left panel — Branding ── */}
        <div className="hidden md:flex flex-col justify-between p-10 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800">
          
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
              Phân tích tài liệu<br />thông minh với AI
            </h2>
            <p className="text-blue-100/80 text-sm leading-relaxed mb-8">
              Tải lên PDF & DOCX, đặt câu hỏi và nhận câu trả lời chính xác từ nội dung tài liệu
            </p>

            {/* Feature pills */}
            <div className="flex flex-col gap-2.5">
              {[
                { icon: FileText, label: "Hỗ trợ PDF & DOCX, tối đa 5 GB" },
                { icon: MessageSquare, label: "RAG thông minh" },
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
            <div className="w-2.5 h-2.5 rounded-full bg-white/80" />
            <div
              title="Trang Đăng ký"
              onClick={() => navigate("/register")}
              className="cursor-pointer w-2.5 h-2.5 rounded-full bg-white/30 hover:bg-white/60 transition-colors"
            />
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

            <LoginForm />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;