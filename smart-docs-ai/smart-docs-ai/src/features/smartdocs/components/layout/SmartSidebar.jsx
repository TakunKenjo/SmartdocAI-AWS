import { useEffect, useContext, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router";
import { BrainCircuit, RefreshCw, Sun, Moon, PanelLeftClose, PanelLeftOpen, LogOut, X } from "lucide-react";
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
import { logout, selectAuthUser } from "@/store/slices/authSlice.js";

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
function SmartSidebar({ mobileOpen = false, onMobileClose = () => {} }) {
  const [collapsed, setCollapsed] = useState(false);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isDark, toggleTheme } = useContext(ThemeContext);
  const ollamaStatus = useSelector(selectOllamaStatus);
  const statusLoading = useSelector(selectStatusLoading);
  const processedFiles = useSelector(selectProcessedFiles);
  const totalChunks = useSelector(selectTotalChunks);
  const authUser = useSelector(selectAuthUser);

  // Helper: lấy 2 chữ cái đầu tên
  const getInitials = (fullname = "") =>
    fullname.trim().split(" ").filter(Boolean).map((n) => n[0]).join("").toUpperCase().slice(0, 2) || "U";

  const handleLogout = async () => {
    await dispatch(logout());
    navigate("/login", { replace: true });
  };

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
    className={[
      "fixed inset-y-0 left-0 z-50",
      mobileOpen ? "translate-x-0" : "-translate-x-full",
      "md:relative md:inset-auto md:z-auto md:translate-x-0",
      "w-72",
      collapsed ? "md:w-20" : "md:w-72",
      "flex-shrink-0 h-full bg-slate-50 dark:bg-slate-950",
      "border-r border-slate-200 dark:border-slate-800",
      "flex flex-col overflow-hidden transition-all duration-300",
    ].join(" ")}
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
            {/* Mobile close button — chỉ hiện trên mobile */}
            <Button
              size="icon"
              variant="ghost"
              className="md:hidden h-8 w-8 mr-1"
              onClick={onMobileClose}
              aria-label="Đóng menu"
            >
              <X className="h-4 w-4" />
            </Button>
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

      {/* ── Logout + Profile footer ── */}
      <div className={`flex-shrink-0 border-t border-slate-200 dark:border-slate-800 ${
        collapsed ? "p-2" : "p-3"
      }`}>
        {collapsed ? (
          <div className="flex flex-col gap-2 items-center">
            {/* Avatar button — collapsed */}
            <button
              onClick={() => { onMobileClose(); navigate("/app/profile"); }}
              title="Hồ sơ cá nhân"
              className="h-9 w-9 rounded-full overflow-hidden flex-shrink-0 ring-2 ring-slate-200 dark:ring-slate-700 hover:ring-blue-400 transition-all focus:outline-none"
            >
              {authUser?.avatar ? (
                <img
                  src={authUser.avatar}
                  alt="Avatar"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center text-[10px] font-bold text-white">
                  {getInitials(authUser?.fullname)}
                </div>
              )}
            </button>
            {/* Logout icon — collapsed */}
            <Button
              size="icon"
              variant="ghost"
              className="h-9 w-9 mx-auto flex text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              onClick={handleLogout}
              title="Đăng xuất"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            {/* Avatar + tên user — expanded */}
            <button
              onClick={() => { onMobileClose(); navigate("/app/profile"); }}
              title="Xem hồ sơ"
              className="h-9 w-9 rounded-full overflow-hidden flex-shrink-0 ring-2 ring-slate-200 dark:ring-slate-700 hover:ring-blue-400 transition-all focus:outline-none"
            >
              {authUser?.avatar ? (
                <img
                  src={authUser.avatar}
                  alt="Avatar"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center text-[10px] font-bold text-white">
                  {getInitials(authUser?.fullname)}
                </div>
              )}
            </button>
            {/* Tên + email */}
            <button
              onClick={() => { onMobileClose(); navigate("/app/profile"); }}
              className="flex-1 min-w-0 text-left hover:opacity-80 transition-opacity"
              title="Xem hồ sơ"
            >
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">
                {authUser?.fullname || authUser?.email?.split("@")[0] || "Người dùng"}
              </p>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                {authUser?.email || ""}
              </p>
            </button>
            {/* Logout button — expanded */}
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 flex-shrink-0 text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              onClick={handleLogout}
              title="Đăng xuất"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
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
