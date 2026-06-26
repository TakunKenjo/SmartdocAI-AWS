import { useEffect, useContext } from "react";
import { useDispatch, useSelector } from "react-redux";
import { BrainCircuit, RefreshCw, Sun, Moon } from "lucide-react";
import { Toggle } from "@/components/ui/toggle";
import { Button } from "@/components/ui/button";
import { ThemeContext } from "@/contexts/ThemeContext.jsx";
import {
  checkOllamaStatus,
  selectOllamaStatus,
  selectStatusLoading,
  selectProcessedFiles,
  selectTotalChunks,
} from "@/store/slices/smartdocSlice.js";

import StatusBadge from "../sidebar/StatusBadge.jsx";
import KpiRow from "../sidebar/KpiRow.jsx";
import ChunkSettings from "../sidebar/ChunkSettings.jsx";
import FileUploader from "../sidebar/FileUploader.jsx";
import FileList from "../sidebar/FileList.jsx";
import ActionButtons from "../sidebar/ActionButtons.jsx";
import ChatHistoryList from "../sidebar/ChatHistoryList.jsx";

/**
 * SmartSidebar — Sidebar riêng của SmartdocAI
 * Layout từ trên xuống: Brand → Status → KPI → Chunk Settings → Upload → File List → Actions → History
 */
function SmartSidebar() {
  const dispatch = useDispatch();
  const { isDark, toggleTheme } = useContext(ThemeContext);
  const ollamaStatus = useSelector(selectOllamaStatus);
  const statusLoading = useSelector(selectStatusLoading);
  const processedFiles = useSelector(selectProcessedFiles);
  const totalChunks = useSelector(selectTotalChunks);

  // Kiểm tra Ollama khi mount
  useEffect(() => {
    if (ollamaStatus === null) {
      dispatch(checkOllamaStatus());
    }
  }, [dispatch, ollamaStatus]);

  const totalPages = processedFiles.reduce((sum, f) => sum + (f.pages || 0), 0);

  return (
    <aside className="w-72 flex-shrink-0 h-full bg-slate-50 dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-0 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-800">

        {/* ── Brand Header ── */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-md shadow-blue-600/30">
              <BrainCircuit className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-50 leading-tight font-sans">
                SmartDocAI
              </h2>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">
                Trợ lý Tài liệu Thông minh
              </p>
            </div>
          </div>

          {/* Theme toggle */}
          <div className="flex items-center gap-1">
            <Toggle
              pressed={isDark}
              onPressedChange={toggleTheme}
              size="sm"
              className="h-7 w-7 p-0"
              aria-label="Toggle theme"
            >
              {isDark ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
            </Toggle>
          </div>
        </div>

        {/* ── Ollama Status ── */}
        <StatusBadge status={ollamaStatus} loading={statusLoading} />

        <Button
          variant="outline"
          size="sm"
          className="w-full text-xs mb-4"
          onClick={() => dispatch(checkOllamaStatus())}
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${statusLoading ? "animate-spin" : ""}`} />
          Kiểm tra kết nối
        </Button>

        {/* ── KPI Stats ── */}
        <KpiRow
          totalFiles={processedFiles.length}
          totalPages={totalPages}
          totalChunks={totalChunks}
        />

        {/* ── Divider + Chunk Settings ── */}
        <SectionLabel label="Cài đặt Chunking" />
        <ChunkSettings />

        {/* ── Divider + Upload ── */}
        <SectionDivider />
        <SectionLabel label="Tải tài liệu lên" />
        <FileUploader />

        {/* ── Divider + Processed Files ── */}
        <SectionDivider />
        <SectionLabel label="Tài liệu đã xử lý" />
        <FileList />

        {/* ── Divider + Actions ── */}
        <SectionDivider />
        <SectionLabel label="Thao tác" />
        <ActionButtons />

        {/* ── Divider + Chat History ── */}
        <SectionDivider />
        <SectionLabel label="Lịch sử hội thoại" />
        <ChatHistoryList />
      </div>
    </aside>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function SectionLabel({ label }) {
  return (
    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 px-0.5 mt-1 mb-2">
      {label}
    </p>
  );
}

function SectionDivider() {
  return (
    <hr className="border-slate-200 dark:border-slate-800 my-3" />
  );
}

export default SmartSidebar;
