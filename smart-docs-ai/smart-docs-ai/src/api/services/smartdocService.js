import axiosClient from "@/api/axiosConfig.js";

// Mock data (dùng khi chưa có backend) 
const MOCK_DELAY = 600; // ms
const mockDelay = (ms = MOCK_DELAY) =>
  new Promise((resolve) => setTimeout(resolve, ms));

const mockHistory = [];
const mockFiles = [];
let mockOllamaOnline = true;

//Service
export const smartdocService = {
  // GET /api/status
  checkStatus: async () => {
    const res = await axiosClient.get("/api/status");
    return {
      data: {
        online: res.data.ollama_status,
        model: res.data.ollama_model
      }
    };
  },

  // POST /api/upload (multipart/form-data)
  uploadDocuments: async (files, chunkSize = 1500, chunkOverlap = 100) => {
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("files", f));
    formData.append("chunk_size", chunkSize);
    formData.append("chunk_overlap", chunkOverlap);
    const res = await axiosClient.post("/api/upload", formData, {
      timeout: 120000,
    });
    return { data: res.data.processed_files };
  },

  // GET /api/files
  getDocuments: async () => {
    return axiosClient.get("/api/files");
  },

  // POST /api/clear-documents
  clearDocuments: async () => {
    return axiosClient.post("/api/clear-documents");
  },

  // POST /api/chat
  sendMessage: async (question, options = {}) => {
    return axiosClient.post("/api/chat", {
      message: question,
      ...options
    }, {
      timeout: 180000,
    });
  },

  // GET /api/history
  getChatHistory: async () => {
    return axiosClient.get("/api/history");
  },

  // POST /api/clear-history
  clearChatHistory: async () => {
    return axiosClient.post("/api/clear-history");
  },
};
