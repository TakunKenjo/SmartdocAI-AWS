import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { CognitoUser, AuthenticationDetails, CognitoUserAttribute } from "amazon-cognito-identity-js";
import { userPool } from "@/api/cognito.js";
import { profileService } from "@/api/services/profileService.js";

// ─── Đăng nhập Cognito ──────────────────────────────────────────────────────────
export const login = createAsyncThunk(
  "auth/login",
  async ({ email, password }, { rejectWithValue }) => {
    return new Promise((resolve, reject) => {
      const authenticationData = {
        Username: email,
        Password: password,
      };
      const authenticationDetails = new AuthenticationDetails(authenticationData);
      const userData = {
        Username: email,
        Pool: userPool,
      };
      const cognitoUser = new CognitoUser(userData);
      
      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (result) => {
          const user = {
            id: result.getIdToken().payload.sub,
            email: result.getIdToken().payload.email,
            fullname: result.getIdToken().payload.name || email.split("@")[0],
            role: "user",
          };
          sessionStorage.setItem("auth_user", JSON.stringify(user));
          resolve(user);
        },
        onFailure: (err) => {
          reject(rejectWithValue(err.message || "Đăng nhập thất bại. Vui lòng kiểm tra lại."));
        },
      });
    });
  }
);

// ─── Đăng ký Cognito ────────────────────────────────────────────────────────────
export const register = createAsyncThunk(
  "auth/register",
  async ({ email, password, fullname, phone, dob }, { rejectWithValue }) => {
    return new Promise((resolve, reject) => {
      const attributeList = [];
      
      // Định dạng SĐT sang chuẩn E.164 của Cognito (ví dụ: +84...)
      let formattedPhone = phone.trim().replace(/\s/g, "");
      if (formattedPhone.startsWith("0")) {
        formattedPhone = "+84" + formattedPhone.substring(1);
      } else if (!formattedPhone.startsWith("+")) {
        formattedPhone = "+84" + formattedPhone;
      }
      
      attributeList.push(new CognitoUserAttribute({ Name: "email", Value: email }));
      attributeList.push(new CognitoUserAttribute({ Name: "name", Value: fullname }));
      attributeList.push(new CognitoUserAttribute({ Name: "phone_number", Value: formattedPhone }));
      attributeList.push(new CognitoUserAttribute({ Name: "birthdate", Value: dob }));
      
      userPool.signUp(email, password, attributeList, null, (err, result) => {
        if (err) {
          reject(rejectWithValue(err.message || "Đăng ký thất bại."));
        } else {
          resolve({ success: true, email });
        }
      });
    });
  }
);

// ─── Xác thực Code Đăng ký Cognito ─────────────────────────────────────────────────
export const confirmCode = createAsyncThunk(
  "auth/confirmCode",
  async ({ email, code }, { rejectWithValue }) => {
    return new Promise((resolve, reject) => {
      const userData = {
        Username: email,
        Pool: userPool,
      };
      const cognitoUser = new CognitoUser(userData);
      
      cognitoUser.confirmRegistration(code, true, (err, result) => {
        if (err) {
          reject(rejectWithValue(err.message || "Mã xác thực không chính xác hoặc đã hết hạn."));
        } else {
          resolve(result);
        }
      });
    });
  }
);

// ─── Đăng xuất Cognito ────────────────────────────────────────────────────────────
export const logout = createAsyncThunk("auth/logout", async () => {
  const cognitoUser = userPool.getCurrentUser();
  if (cognitoUser) {
    cognitoUser.signOut();
  }
  sessionStorage.removeItem("auth_user");
  return null;
});

// ─── Khôi phục session từ sessionStorage khi reload ───────────────────────────
const restoreUser = () => {
  try {
    const raw = sessionStorage.getItem("auth_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

// ─── Initial State ────────────────────────────────────────────────────────────
const initialState = {
  user: restoreUser(),
  isAuthenticated: !!restoreUser(),
  isLoading: false,
  error: null,
};

// ════════════════════════════════════════════════════════════════════════════════
// PROFILE — Thunks bổ sung cho feature/profile (chỉ thêm vào, không sửa code trên)
// ════════════════════════════════════════════════════════════════════════════════

// ─── Cập nhật Avatar ─────────────────────────────────────────────────────────
export const updateAvatar = createAsyncThunk(
  "auth/updateAvatar",
  async ({ userId, avatar }, { rejectWithValue }) => {
    try {
      await profileService.updateAvatar(userId, avatar);
      return avatar; // trả về base64 để cập nhật state.user.avatar
    } catch (err) {
      return rejectWithValue(err.response?.data?.message || err.message || "Cập nhật ảnh thất bại.");
    }
  }
);

// ─── Cập nhật thông tin cá nhân (Cognito updateAttributes) ────────────────────
export const updatePersonalInfo = createAsyncThunk(
  "auth/updatePersonalInfo",
  async ({ userId, fullname, email, phone, dob }, { rejectWithValue }) => {
    return new Promise((resolve, reject) => {
      const cognitoUser = userPool.getCurrentUser();
      if (!cognitoUser) {
        return reject(rejectWithValue("Không tìm thấy session. Vui lòng đăng nhập lại."));
      }
      cognitoUser.getSession((err, session) => {
        if (err || !session) {
          return reject(rejectWithValue("Session hết hạn. Vui lòng đăng nhập lại."));
        }
        // Định dạng SĐT sang chuẩn E.164
        let formattedPhone = (phone || "").trim().replace(/\s/g, "");
        if (formattedPhone.startsWith("0")) {
          formattedPhone = "+84" + formattedPhone.substring(1);
        } else if (formattedPhone && !formattedPhone.startsWith("+")) {
          formattedPhone = "+84" + formattedPhone;
        }
        const attributeList = [
          new CognitoUserAttribute({ Name: "name",  Value: fullname }),
          new CognitoUserAttribute({ Name: "email", Value: email }),
        ];
        if (formattedPhone) {
          attributeList.push(new CognitoUserAttribute({ Name: "phone_number", Value: formattedPhone }));
        }
        if (dob) {
          attributeList.push(new CognitoUserAttribute({ Name: "birthdate", Value: dob }));
        }
        cognitoUser.updateAttributes(attributeList, (updateErr) => {
          if (updateErr) reject(rejectWithValue(updateErr.message || "Cập nhật thất bại."));
          else resolve({ fullname, email, phone, dob });
        });
      });
    });
  }
);

// ─── Đổi mật khẩu (Cognito changePassword) ───────────────────────────────────
export const changePassword = createAsyncThunk(
  "auth/changePassword",
  async ({ currentPassword, newPassword }, { rejectWithValue }) => {
    return new Promise((resolve, reject) => {
      const cognitoUser = userPool.getCurrentUser();
      if (!cognitoUser) {
        return reject(rejectWithValue("Không tìm thấy session. Vui lòng đăng nhập lại."));
      }
      cognitoUser.getSession((err, session) => {
        if (err || !session) {
          return reject(rejectWithValue("Session hết hạn. Vui lòng đăng nhập lại."));
        }
        cognitoUser.changePassword(currentPassword, newPassword, (changeErr) => {
          if (changeErr) reject(rejectWithValue(changeErr.message || "Đổi mật khẩu thất bại."));
          else resolve(true);
        });
      });
    });
  }
);

// ─── Slice ────────────────────────────────────────────────────────────────────
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    clearAuthError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // ── Login ──
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.error = action.payload;
      });

    // ── Register ──
    builder
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });

    // ── Confirm Code ──
    builder
      .addCase(confirmCode.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(confirmCode.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(confirmCode.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });

    // ── Logout ──
    builder.addCase(logout.fulfilled, (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.error = null;
    });

    // ════════════════════════════════════════
    // PROFILE — Extra reducers bổ sung
    // ════════════════════════════════════════

    // ── Update Avatar ──
    builder.addCase(updateAvatar.fulfilled, (state, action) => {
      if (state.user) {
        state.user.avatar = action.payload;
        sessionStorage.setItem("auth_user", JSON.stringify(state.user));
      }
    });

    // ── Update Personal Info ──
    builder.addCase(updatePersonalInfo.fulfilled, (state, action) => {
      if (state.user) {
        const { fullname, email, phone, dob } = action.payload;
        state.user.fullname = fullname;
        state.user.email    = email;
        state.user.phone    = phone;
        state.user.dob      = dob;
        sessionStorage.setItem("auth_user", JSON.stringify(state.user));
      }
    });

    // ── Change Password — không cần cập nhật state ──
  },
});

// ─── Selectors ────────────────────────────────────────────────────────────────
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectAuthUser       = (state) => state.auth.user;
export const selectAuthLoading    = (state) => state.auth.isLoading;
export const selectAuthError      = (state) => state.auth.error;

// ── Profile selectors bổ sung ──
// selectCurrentUser: alias của selectAuthUser, dùng trong feature/profile
export const selectCurrentUser = (state) => state.auth.user;

export const { clearAuthError } = authSlice.actions;
export default authSlice.reducer;
