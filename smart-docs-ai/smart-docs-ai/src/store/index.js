import { configureStore } from "@reduxjs/toolkit";
import smartdocReducer from "@/store/slices/smartdocSlice.js";

export const store = configureStore({
  reducer: {
    smartdoc: smartdocReducer,
  },
});
