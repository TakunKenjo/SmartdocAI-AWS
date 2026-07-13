import axiosClient from "@/api/axiosConfig.js";

/**
 * profileService — API calls liên quan đến hồ sơ người dùng
 * Dùng axiosClient (đã có Cognito token interceptor)
 */
export const profileService = {
  /**
   * PUT /api/profile/avatar
   * Gửi avatar dạng base64 lên backend để lưu trữ
   * @param {string} userId - Cognito sub (user ID)
   * @param {string} avatarBase64 - Chuỗi base64 "data:image/jpeg;base64,..."
   */
  updateAvatar: async (userId, avatarBase64) => {
    const res = await axiosClient.put("/api/profile/avatar", {
      user_id: userId,
      avatar: avatarBase64,
    });
    return res.data;
  },
};
