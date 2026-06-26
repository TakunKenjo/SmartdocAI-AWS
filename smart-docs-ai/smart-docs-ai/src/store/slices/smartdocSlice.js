import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { smartdocService } from "@/api/services/smartdocService.js";

// ─── Initial State ────────────────────────────────────────────────────────────
const initialState = {
  // Status
  ollamaStatus: null, // null | { online: bool, model: string }
  statusLoading: false,

  // Documents
  processedFiles: [], // [{name, pages, chunks, size}]
  totalChunks: 0,
  isProcessing: false,
  processingError: null,

  // Chat
  chatHistory: [], // [{role, content, sources, searchMode, selfRagMeta, coRagMeta}]
  isChatLoading: false,
  chatError: null,

  // Chunk settings
  chunkSize: 1500,
  chunkOverlap: 100,

  // Search options
  hybridEnabled: false,
  rerankerEnabled: false,
  selfRagEnabled: false,
  selfRagConfig: {
    queryRewrite: true,
    relevanceFilter: true,
    answerGrading: true,
  },
  coRagEnabled: false,
  coRagConfig: {
    strategy: "voting",
    semantic: true,
    keyword: true,
    conceptual: true,
  },
  activeFileFilter: [],
};

// ─── Selectors ────────────────────────────────────────────────────────────────
export const selectOllamaStatus = (state) => state.smartdoc.ollamaStatus;
export const selectStatusLoading = (state) => state.smartdoc.statusLoading;
export const selectProcessedFiles = (state) => state.smartdoc.processedFiles;
export const selectTotalChunks = (state) => state.smartdoc.totalChunks;
export const selectIsProcessing = (state) => state.smartdoc.isProcessing;
export const selectProcessingError = (state) => state.smartdoc.processingError;
export const selectChatHistory = (state) => state.smartdoc.chatHistory;
export const selectIsChatLoading = (state) => state.smartdoc.isChatLoading;
export const selectChatError = (state) => state.smartdoc.chatError;
export const selectChunkSize = (state) => state.smartdoc.chunkSize;
export const selectChunkOverlap = (state) => state.smartdoc.chunkOverlap;
export const selectHybridEnabled = (state) => state.smartdoc.hybridEnabled;
export const selectRerankerEnabled = (state) => state.smartdoc.rerankerEnabled;
export const selectSelfRagEnabled = (state) => state.smartdoc.selfRagEnabled;
export const selectSelfRagConfig = (state) => state.smartdoc.selfRagConfig;
export const selectCoRagEnabled = (state) => state.smartdoc.coRagEnabled;
export const selectCoRagConfig = (state) => state.smartdoc.coRagConfig;
export const selectActiveFileFilter = (state) => state.smartdoc.activeFileFilter;

// ─── Thunks ───────────────────────────────────────────────────────────────────
export const checkOllamaStatus = createAsyncThunk(
  "smartdoc/checkStatus",
  async (_, { rejectWithValue }) => {
    try {
      const res = await smartdocService.checkStatus();
      return res.data;
    } catch (err) {
      return rejectWithValue(err?.message || "Không thể kết nối");
    }
  }
);

export const uploadDocuments = createAsyncThunk(
  "smartdoc/uploadDocuments",
  async ({ files, chunkSize, chunkOverlap }, { rejectWithValue }) => {
    try {
      const res = await smartdocService.uploadDocuments(files, chunkSize, chunkOverlap);
      return res.data;
    } catch (err) {
      return rejectWithValue(err?.response?.data?.message || err?.message || "Upload thất bại!");
    }
  }
);

export const clearDocuments = createAsyncThunk(
  "smartdoc/clearDocuments",
  async (_, { rejectWithValue }) => {
    try {
      await smartdocService.clearDocuments();
    } catch (err) {
      return rejectWithValue(err?.message || "Xóa tài liệu thất bại!");
    }
  }
);

export const sendMessage = createAsyncThunk(
  "smartdoc/sendMessage",
  async ({ question, options }, { rejectWithValue }) => {
    try {
      const res = await smartdocService.sendMessage(question, options);
      return { question, ...res.data };
    } catch (err) {
      return rejectWithValue(err?.response?.data?.message || err?.message || "Gửi tin nhắn thất bại!");
    }
  }
);

export const clearChatHistory = createAsyncThunk(
  "smartdoc/clearChatHistory",
  async (_, { rejectWithValue }) => {
    try {
      await smartdocService.clearChatHistory();
    } catch (err) {
      return rejectWithValue(err?.message || "Xóa lịch sử thất bại!");
    }
  }
);

// ─── Slice ────────────────────────────────────────────────────────────────────
const smartdocSlice = createSlice({
  name: "smartdoc",
  initialState,
  reducers: {
    setChunkSize: (state, action) => {
      state.chunkSize = action.payload;
    },
    setChunkOverlap: (state, action) => {
      state.chunkOverlap = action.payload;
    },
    setHybridEnabled: (state, action) => {
      state.hybridEnabled = action.payload;
    },
    setRerankerEnabled: (state, action) => {
      state.rerankerEnabled = action.payload;
    },
    setSelfRagEnabled: (state, action) => {
      state.selfRagEnabled = action.payload;
      // Xung đột với Co-RAG
      if (action.payload) state.coRagEnabled = false;
    },
    setSelfRagConfig: (state, action) => {
      state.selfRagConfig = { ...state.selfRagConfig, ...action.payload };
    },
    setCoRagEnabled: (state, action) => {
      state.coRagEnabled = action.payload;
      // Xung đột với Self-RAG
      if (action.payload) state.selfRagEnabled = false;
    },
    setCoRagConfig: (state, action) => {
      state.coRagConfig = { ...state.coRagConfig, ...action.payload };
    },
    setActiveFileFilter: (state, action) => {
      state.activeFileFilter = action.payload;
    },
    // Thêm user message ngay vào history (optimistic update)
    addUserMessage: (state, action) => {
      state.chatHistory.push({ role: "user", content: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      // ── Check Status ──
      .addCase(checkOllamaStatus.pending, (state) => {
        state.statusLoading = true;
      })
      .addCase(checkOllamaStatus.fulfilled, (state, action) => {
        state.statusLoading = false;
        state.ollamaStatus = action.payload;
      })
      .addCase(checkOllamaStatus.rejected, (state) => {
        state.statusLoading = false;
        state.ollamaStatus = { online: false, model: "" };
      })

      // ── Upload Documents ──
      .addCase(uploadDocuments.pending, (state) => {
        state.isProcessing = true;
        state.processingError = null;
      })
      .addCase(uploadDocuments.fulfilled, (state, action) => {
        state.isProcessing = false;
        const newFiles = action.payload;
        state.processedFiles.push(...newFiles);
        state.totalChunks = state.processedFiles.reduce((sum, f) => sum + (f.chunks || 0), 0);
      })
      .addCase(uploadDocuments.rejected, (state, action) => {
        state.isProcessing = false;
        state.processingError = action.payload;
      })

      // ── Clear Documents ──
      .addCase(clearDocuments.fulfilled, (state) => {
        state.processedFiles = [];
        state.totalChunks = 0;
        state.activeFileFilter = [];
      })

      // ── Send Message ──
      .addCase(sendMessage.pending, (state) => {
        state.isChatLoading = true;
        state.chatError = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isChatLoading = false;
        const { answer, sources, search_mode, self_rag_meta, co_rag_meta, question } = action.payload;
        // Ghi đè user message cuối (đã add optimistic) và thêm assistant message
        state.chatHistory.push({
          role: "assistant",
          content: answer,
          sources: sources || [],
          searchMode: search_mode,
          selfRagMeta: self_rag_meta,
          coRagMeta: co_rag_meta,
          questionCtx: question,
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isChatLoading = false;
        state.chatError = action.payload;
        // Xóa user message optimistic nếu thất bại
        if (state.chatHistory.length > 0 && state.chatHistory.at(-1).role === "user") {
          state.chatHistory.pop();
        }
      })

      // ── Clear Chat History ──
      .addCase(clearChatHistory.fulfilled, (state) => {
        state.chatHistory = [];
      });
  },
});

export const {
  setChunkSize,
  setChunkOverlap,
  setHybridEnabled,
  setRerankerEnabled,
  setSelfRagEnabled,
  setSelfRagConfig,
  setCoRagEnabled,
  setCoRagConfig,
  setActiveFileFilter,
  addUserMessage,
} = smartdocSlice.actions;

export default smartdocSlice.reducer;
