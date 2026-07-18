import axiosClient from "@/api/axiosConfig.js";

/**
 * [SmartDocAI-Profile] profileService — API calls liên quan đến hồ sơ người dùng
 * Dùng axiosClient (đã có token interceptor tự động gắn Bearer token)
 * Backend: http://localhost:8000/api/profile/*
 */
export const profileService = {
  /**
   * GET /api/profile
   * Lấy thông tin hồ sơ của người dùng hiện tại
   */
  getProfile: async () => {
    const res = await axiosClient.get("/api/profile");
    return res.data;
  },

  /**
   * PUT /api/profile/personal-info
   * Cập nhật thông tin cá nhân: fullname, email, phone, dob
   * @param {object} data - { fullname, email, phone, dob }
   */
  updatePersonalInfo: async (data) => {
    const res = await axiosClient.put("/api/profile/personal-info", {
      fullname: data.fullname,
      email: data.email,
      phone: data.phone,
      dob: data.dob,
    });
    return res.data;
  },

  /**
   * PUT /api/profile/avatar
   * Gửi avatar dạng base64 lên backend để lưu trữ (DynamoDB nếu < 300KB, S3 nếu > 300KB)
   * @param {string} avatarBase64 - Chuỗi base64 "data:image/jpeg;base64,..."
   */
  updateAvatar: async (avatarBase64) => {
    const res = await axiosClient.put("/api/profile/avatar", {
      avatar: avatarBase64,
    });
    return res.data;
  },

  /**
   * POST /api/profile/change-password
   * Đổi mật khẩu
   * @param {object} data - { currentPassword, newPassword, isGoogleUser }
   */
  changePassword: async (data) => {
    const res = await axiosClient.post("/api/profile/change-password", {
      current_password: data.currentPassword,
      new_password: data.newPassword,
      is_google_user: data.isGoogleUser,
    });
    return res.data;
  },
};
