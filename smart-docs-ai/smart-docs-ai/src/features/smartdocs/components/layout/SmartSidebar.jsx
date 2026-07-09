import { useEffect, useContext, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { BrainCircuit, RefreshCw, Sun, Moon, PanelLeftClose, PanelLeftOpen, } from "lucide-react";
import { Toggle } from "@/components/ui/toggle";
import { Button } from "@/components/ui/button";
import { ThemeContext } from "@/contexts/ThemeContext.jsx";
import {
  checkOllamaStatus,
  fetchProcessedFiles,
  fetchChatHistory,
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
  const [collapsed, setCollapsed] = useState(false);
  const dispatch = useDispatch();
  const { isDark, toggleTheme } = useContext(ThemeContext);
  const ollamaStatus = useSelector(selectOllamaStatus);
  const statusLoading = useSelector(selectStatusLoading);
  const processedFiles = useSelector(selectProcessedFiles);
  const totalChunks = useSelector(selectTotalChunks);

  // Kiểm tra Ollama, danh sách tài liệu và lịch sử chat khi mount
  useEffect(() => {
    if (ollamaStatus === null) {
      dispatch(checkOllamaStatus());
    }
    dispatch(fetchProcessedFiles());
    dispatch(fetchChatHistory());
  }, [dispatch, ollamaStatus]);

  const totalPages = processedFiles.reduce((sum, f) => sum + (f.pages || 0), 0);

  return (
  <aside
    className={`${
      collapsed ? "w-20" : "w-72"
    } flex-shrink-0 h-full bg-slate-50 dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden transition-all duration-300`}
  >      
      <div
        className={`flex-1 overflow-y-auto py-5 transition-all ${
            collapsed ? "px-2" : "px-4"
        }`}
      >

        {/* ── Brand Header ── */}
        <div
          className={`flex ${
            collapsed ? "flex-col items-center gap-3" : "items-center justify-between"
          } mb-5`}
        >
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-md shadow-blue-600/30">
              <BrainCircuit className="h-5 w-5 text-white" />
            </div>

            {!collapsed && (
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-50">
                  SmartDocAI
                </h2>
                <p className="text-[10px] text-slate-400 dark:text-slate-500">
                  Trợ lý Tài liệu Thông minh
                </p>
              </div>
            )}
          </div>

          {/* Buttons */}
          <div
            className={`flex ${
              collapsed ? "flex-col gap-2 mt-2" : "items-center gap-1"
            }`}
          >
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8"
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? (
                <PanelLeftOpen className="h-4 w-4" />
              ) : (
                <PanelLeftClose className="h-4 w-4" />
              )}
            </Button>

            <Toggle
              pressed={isDark}
              onPressedChange={toggleTheme}
              size="sm"
              className="h-8 w-8 p-0"
              aria-label="Toggle theme"
            >
              {isDark ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Sun className="h-4 w-4" />
              )}
            </Toggle>
          </div>
        </div>

        {/* ── Ollama Status ── */}
        {!collapsed && (<StatusBadge status={ollamaStatus} loading={statusLoading} /> )}


         {!collapsed && (<Button
          variant="outline"
          size="sm"
          className="w-full text-xs mb-4"
          onClick={() => dispatch(checkOllamaStatus())}
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${statusLoading ? "animate-spin" : ""}`} />
          Kiểm tra kết nối
        </Button> )}

        {/* ── KPI Stats ── */}
         {!collapsed && (<KpiRow
          totalFiles={processedFiles.length}
          totalPages={totalPages}
          totalChunks={totalChunks}
        />)}

        {/* ── Divider + Chunk Settings ── */}
        {!collapsed && (<SectionLabel label="Cài đặt Chunking" />)}
        {!collapsed && (<ChunkSettings />)}

        {/* ── Divider + Upload ── */}
        {!collapsed && (<SectionDivider />)}
        {!collapsed && (<SectionLabel label="Tải tài liệu lên" />)}
        {!collapsed && (<FileUploader />)}

        {/* ── Divider + Processed Files ── */}
        {!collapsed && (<SectionDivider />)}
        {!collapsed && (<SectionLabel label="Tài liệu đã xử lý" />)}
        {!collapsed && (<FileList />)}

        {/* ── Divider + Actions ── */}
        {!collapsed && (<SectionDivider />)}
        {!collapsed && (<SectionLabel label="Thao tác" />)}
        {!collapsed && (<ActionButtons />)}

        {/* ── Divider + Chat History ── */}
        {!collapsed && (<SectionDivider />)}
        {!collapsed && (<SectionLabel label="Lịch sử hội thoại" />)}
        {!collapsed && (<ChatHistoryList />)}
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
