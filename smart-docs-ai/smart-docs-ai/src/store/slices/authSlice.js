import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";

// ─── Mock delay ────────────────────────────────────────────────────────────────
const delay = (ms) => new Promise((res) => setTimeout(res, ms));

// ─── Mock "đăng nhập" — Không cần tài khoản thật ──────────────────────────────
// Chỉ validate form FE, sau đó giả lập login thành công
export const login = createAsyncThunk(
  "auth/login",
  async ({ email, password }, { rejectWithValue }) => {
    try {
      await delay(800); // giả lập call API

      // Validate cơ bản ở đây (BE không được chỉnh sửa)
      if (!email || !password) {
        return rejectWithValue("Email và mật khẩu không được để trống.");
      }

      // Luôn cho đăng nhập thành công (mock)
      const mockUser = {
        id: "mock-user-001",
        email,
        fullname: email.split("@")[0],
        role: "user",
      };

      // Lưu vào sessionStorage để persist trong tab
      sessionStorage.setItem("auth_user", JSON.stringify(mockUser));

      return mockUser;
    } catch (err) {
      return rejectWithValue(err?.message || "Đăng nhập thất bại.");
    }
  }
);

// ─── Mock "đăng ký" ────────────────────────────────────────────────────────────
export const register = createAsyncThunk(
  "auth/register",
  async (formData, { rejectWithValue }) => {
    try {
      await delay(900);

      // Lưu thông tin đăng ký vào localStorage (mock DB)
      const users = JSON.parse(localStorage.getItem("mock_users") || "[]");
      const exists = users.find((u) => u.email === formData.email);
      if (exists) {
        return rejectWithValue("Email này đã được đăng ký.");
      }

      const newUser = {
        id: `user-${Date.now()}`,
        email: formData.email,
        fullname: formData.fullname,
        phone: formData.phone,
        dob: formData.dob,
      };

      users.push(newUser);
      localStorage.setItem("mock_users", JSON.stringify(users));

      return { success: true };
    } catch (err) {
      return rejectWithValue(err?.message || "Đăng ký thất bại.");
    }
  }
);

// ─── Logout ────────────────────────────────────────────────────────────────────
export const logout = createAsyncThunk("auth/logout", async () => {
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
  user: restoreUser(),                   // Restore từ session
  isAuthenticated: !!restoreUser(),      // true nếu có session
  isLoading: false,
  error: null,
};

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

    // ── Logout ──
    builder.addCase(logout.fulfilled, (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.error = null;
    });
  },
});

// ─── Selectors ────────────────────────────────────────────────────────────────
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectAuthUser       = (state) => state.auth.user;
export const selectAuthLoading    = (state) => state.auth.isLoading;
export const selectAuthError      = (state) => state.auth.error;

export const { clearAuthError } = authSlice.actions;
export default authSlice.reducer;
