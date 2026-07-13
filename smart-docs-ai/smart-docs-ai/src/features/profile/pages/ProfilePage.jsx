import { useNavigate } from "react-router";
import { ArrowLeft } from "lucide-react";
import { useSelector } from "react-redux";
import { selectCurrentUser } from "@/store/slices/authSlice";
import { Button } from "@/components/ui/button";
import ProfileAvatar from "../components/ProfileAvatar";
import PersonalInfoTab from "../components/PersonalInfoTab";
import SecurityTab from "../components/SecurityTab";

import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

// Helper: lấy chữ cái đầu tên
const getInitials = (fullname = "") =>
  fullname
    .trim()
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "U";

const ProfilePage = () => {
  const navigate = useNavigate();
  const user = useSelector(selectCurrentUser);

  return (
    // auth-page → CSS override cho phép scroll
    <div className="auth-page min-h-screen bg-slate-50 dark:bg-slate-950">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-5">

        {/* ── Header bar ── */}
        <div className="flex items-center gap-3 pb-1 border-b border-slate-200 dark:border-slate-800">
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
            {/* Avatar mini */}
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt="Avatar"
                className="w-8 h-8 rounded-full object-cover ring-2 ring-white dark:ring-slate-800 shadow-sm flex-shrink-0"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-sm flex-shrink-0">
                {getInitials(user?.fullname)}
              </div>
            )}
            <div>
              <h1 className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-tight">
                {user?.fullname || user?.email?.split("@")[0] || "Hồ sơ"}
              </h1>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">
                {user?.email || ""}
              </p>
            </div>
          </div>
        </div>

        {/* ── Main content grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* ── Left: Avatar card ── */}
          <div className="lg:col-span-1">
            <ProfileAvatar />
          </div>

          {/* ── Right: Tabs ── */}
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
  );
};

export default ProfilePage;