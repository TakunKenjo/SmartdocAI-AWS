import axios from "axios";
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
        model: res.data.ollama_model,
        modelReady: res.data.model_ready || false,
      }
    };
  },

  // POST /api/upload-url
  getUploadUrl: async (filename, contentType) => {
    const res = await axiosClient.post("/api/upload-url", {
      filename,
      content_type: contentType || "application/octet-stream"
    });
    return res.data;
  },

  // PUT file binary directly to S3 via Presigned URL
  uploadFileToS3: async (uploadUrl, file) => {
    await axios.put(uploadUrl, file, {
      headers: {
        "Content-Type": file.type || "application/octet-stream",
      },
      timeout: 300000,
    });
  },

  // POST /api/process
  processDocument: async (filename, s3Key, chunkSize = 1500, chunkOverlap = 100) => {
    const res = await axiosClient.post("/api/process", {
      filename,
      s3_key: s3Key,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    }, {
      timeout: 180000,
    });
    return { data: res.data.processed_files };
  },

  // POST /api/upload (multipart/form-data fallback)
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
