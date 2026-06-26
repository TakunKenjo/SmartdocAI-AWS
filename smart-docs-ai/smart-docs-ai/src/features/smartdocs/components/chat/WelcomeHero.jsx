import { BrainCircuit } from "lucide-react";

/**
 * WelcomeHero — Màn hình chào mừng khi chưa có chat
 * Hai trạng thái: chưa có tài liệu | đã có tài liệu sẵn sàng chat
 */
function WelcomeHero({ hasDocs }) {
  return (
    <div className="flex flex-col items-center justify-center text-center px-8 py-12 flex-1 min-h-0">
      {/* Icon */}
         <div className="relative flex justify-center mb-6">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg">
              <span className="text-4xl font-bold text-white">
                  <BrainCircuit className="h-8 w-8 text-white  flex items-center justify-center" />
              </span>
            </div>
            <div className="absolute w-20 h-20 rounded-3xl bg-blue-400 opacity-30 animate-ping" />
          </div>

      {hasDocs ? (
        <>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 mb-2">
            Sẵn sàng trò chuyện!
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-sm">
            Tài liệu đã được xử lý thành công. Hãy đặt câu hỏi về nội dung
            tài liệu trong khung chat bên dưới.
          </p>
        </>
      ) : (
        <>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 mb-2">
            Chào mừng đến SmartDocAI
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-sm mb-6">
            Trợ lý AI thông minh giúp bạn phân tích và hỏi đáp nội dung
            tài liệu PDF &amp; DOCX. Tải tài liệu lên và bắt đầu trò chuyện ngay!
          </p>

          {/* Steps */}
          <div className="flex flex-wrap gap-2 justify-center">
            {[
              { num: "1", text: "Tải file PDF hoặc DOCX lên" },
              { num: "2", text: "Chờ hệ thống xử lý" },
              { num: "3", text: "Đặt câu hỏi trong chat" },
            ].map(({ num, text }) => (
              <div
                key={num}
                className="flex items-center gap-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-600 dark:text-slate-400 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-all"
              >
                <span className="w-6 h-6 rounded-full bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {num}
                </span>
                {text}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default WelcomeHero;
