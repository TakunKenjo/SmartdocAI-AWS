import { configureStore } from "@reduxjs/toolkit";
import smartdocReducer from "@/store/slices/smartdocSlice.js";
import authReducer from "@/store/slices/authSlice.js";

export const store = configureStore({
  reducer: {
    smartdoc: smartdocReducer,
    auth: authReducer,
  },
});
