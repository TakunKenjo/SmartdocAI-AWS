import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router";
import { useSelector } from "react-redux";
import { selectCurrentUser } from "@/store/slices/authSlice";
import { Button } from "@/components/ui/button";
import SmartSidebar from "@/features/smartdocs/components/layout/SmartSidebar.jsx";
import ProfileAvatar from "../components/ProfileAvatar";
import PersonalInfoTab from "../components/PersonalInfoTab";
import SecurityTab from "../components/SecurityTab";

import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

// Helper: chữ cái đầu tên
const getInitials = (fullname = "") =>
  fullname.trim().split(" ").filter(Boolean).map((n) => n[0]).join("").toUpperCase().slice(0, 2) || "U";

const ProfilePage = () => {
  const navigate = useNavigate();
  const user = useSelector(selectCurrentUser);

  // Mobile sidebar drawer — giống SmartdocPage
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    // Cùng cấu trúc layout với SmartdocPage: flex h-full
    <div className="flex h-full w-full overflow-hidden relative">

      {/* ── Mobile backdrop ── */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Sidebar (dùng chung với SmartdocPage) ── */}
      <SmartSidebar
        mobileOpen={mobileSidebarOpen}
        onMobileClose={() => setMobileSidebarOpen(false)}
      />

      {/* ── Profile content area ── */}
      <div className="flex flex-col flex-1 min-h-0 bg-slate-50 dark:bg-slate-950">

        {/* Mobile top bar — giống ChatArea */}
        <div className="flex md:hidden flex-shrink-0 items-center justify-between px-3 py-2.5 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="h-9 w-9 flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Mở menu"
            >
              {/* Hamburger icon inline */}
              <svg className="h-5 w-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="font-bold text-sm text-slate-900 dark:text-slate-50">Hồ sơ cá nhân</span>
          </div>
          <div className="w-9" aria-hidden="true" />
        </div>

        {/* ── Scrollable content ── */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-5">

            {/* Header bar */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/app")}
                className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100 -ml-1 h-8"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Quay lại</span>
              </Button>

              <div className="flex items-center gap-2.5">
                {user?.avatar ? (
                  <img
                    src={user.avatar}
                    alt="Avatar"
                    className="w-8 h-8 rounded-full object-cover ring-2 ring-white dark:ring-slate-800 shadow-sm flex-shrink-0"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-sm shadow-blue-600/30 flex-shrink-0">
                    {getInitials(user?.fullname)}
                  </div>
                )}
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-tight">
                    {user?.fullname || user?.email?.split("@")[0] || "Hồ sơ"}
                  </p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500">
                    {user?.email || ""}
                  </p>
                </div>
              </div>
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

              {/* Avatar card */}
              <div className="lg:col-span-1">
                <ProfileAvatar />
              </div>

              {/* Tabs */}
              <div className="lg:col-span-2">
                <Tabs defaultValue="personal">
                  <TabsList className="w-full sm:w-auto mb-4 bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl p-1 h-auto">
                    <TabsTrigger
                      value="personal"
                      className="flex-1 sm:flex-none text-xs font-semibold px-4 py-2 rounded-lg
                        text-slate-500 dark:text-slate-400
                        data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900
                        data-[state=active]:text-slate-800 dark:data-[state=active]:text-slate-100
                        data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-slate-200 dark:data-[state=active]:border-slate-700
                        transition-all"
                    >
                      Thông tin cá nhân
                    </TabsTrigger>
                    <TabsTrigger
                      value="security"
                      className="flex-1 sm:flex-none text-xs font-semibold px-4 py-2 rounded-lg
                        text-slate-500 dark:text-slate-400
                        data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900
                        data-[state=active]:text-slate-800 dark:data-[state=active]:text-slate-100
                        data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-slate-200 dark:data-[state=active]:border-slate-700
                        transition-all"
                    >
                      Bảo mật
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="personal">
                    <PersonalInfoTab />
                  </TabsContent>

                  <TabsContent value="security">
                    <SecurityTab />
                  </TabsContent>
                </Tabs>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;