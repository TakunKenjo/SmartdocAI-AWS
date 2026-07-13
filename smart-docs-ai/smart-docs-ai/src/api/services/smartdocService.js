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
    // JSON thực tế: { online, provider, model, embedding_provider, embedding_model,
    //                 total_files, total_pages, total_chunks, model_ready }
    return {
      data: {
        online:    res.data.online,                    // ← đúng field name
        model:     res.data.model     || "",           // ← đúng field name
        provider:  res.data.provider  || "LLM",       // ← thêm provider
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




  // GET /api/files
  getDocuments: async () => {
    return axiosClient.get("/api/files");
  },

  // POST /api/clear-documents
  clearDocuments: async () => {
    return axiosClient.post("/api/clear-documents");
  },

  // POST /api/delete-document
  deleteDocument: async (filename) => {
    return axiosClient.post("/api/delete-document", { filename });
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
