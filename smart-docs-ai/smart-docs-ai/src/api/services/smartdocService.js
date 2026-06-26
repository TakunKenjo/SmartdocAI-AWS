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
    await mockDelay(300);
    return { data: { online: mockOllamaOnline, model: "llama3.2:3b" } };
    // return axiosClient.get("/api/smartdoc/status");
  },

  // POST /api/smartdoc/documents/upload (multipart/form-data)
  uploadDocuments: async (files, chunkSize = 1500, chunkOverlap = 100) => {
    await mockDelay(1500);
    const result = Array.from(files).map((f) => ({
      name: f.name,
      pages: Math.floor(Math.random() * 50) + 5,
      chunks: Math.floor(Math.random() * 120) + 20,
      size: f.size,
    }));
    mockFiles.push(...result);
    return { data: result };
    // const formData = new FormData();
    // Array.from(files).forEach((f) => formData.append("files", f));
    // formData.append("chunk_size", chunkSize);
    // formData.append("chunk_overlap", chunkOverlap);
    // return axiosClient.post("/api/smartdoc/documents/upload", formData, {
    //   headers: { "Content-Type": "multipart/form-data" },
    //   timeout: 120000,
    // });
  },

  // GET /api/smartdoc/documents
  getDocuments: async () => {
    await mockDelay(300);
    return { data: mockFiles };
    // return axiosClient.get("/api/smartdoc/documents");
  },

  // DELETE /api/smartdoc/documents
  clearDocuments: async () => {
    await mockDelay(400);
    mockFiles.length = 0;
    return { data: { success: true } };
    // return axiosClient.delete("/api/smartdoc/documents");
  },

  // POST /api/smartdoc/chat
  sendMessage: async (question, options = {}) => {
    await mockDelay(1800);
    const mockAnswer = `Đây là câu trả lời mẫu cho câu hỏi: "${question}". 

SmartDocAI đã phân tích tài liệu và tìm thấy các đoạn liên quan. Hệ thống sử dụng ${
      options.selfRagEnabled
        ? "Self-RAG"
        : options.coRagEnabled
          ? "Co-RAG"
          : options.hybridEnabled
            ? "Hybrid Search"
            : "Vector Search"
    } để truy xuất thông tin.

Nội dung được trích xuất từ các tài liệu bạn đã tải lên, và được xử lý bởi mô hình ngôn ngữ lớn để tạo ra câu trả lời chính xác và đầy đủ nhất có thể.`;

    const mockSources =
      mockFiles.length > 0
        ? [
            {
              file: mockFiles[0]?.name || "document.pdf",
              page: Math.floor(Math.random() * 10) + 1,
              total_pages: mockFiles[0]?.pages || 20,
              file_type: "pdf",
              content:
                "Đây là đoạn nội dung được trích xuất từ tài liệu. Nó chứa thông tin liên quan đến câu hỏi của bạn và được sử dụng để tạo ra câu trả lời.",
              chunk_index: 1,
              score: 0.87,
            },
          ]
        : [];

    return {
      data: {
        answer: mockAnswer,
        sources: mockSources,
        search_mode: options.selfRagEnabled
          ? "self_rag"
          : options.coRagEnabled
            ? "co_rag"
            : options.hybridEnabled
              ? "hybrid"
              : "vector",
        self_rag_meta: options.selfRagEnabled
          ? {
              confidence_score: 0.82,
              is_grounded: true,
              has_hallucination: false,
              grading_feedback: "Câu trả lời dựa chắc chắn trên tài liệu.",
              rewritten_queries: [question, `${question} (variant 1)`, `${question} chi tiết`],
              docs_before_filter: 10,
              docs_after_filter: 4,
            }
          : null,
        co_rag_meta: options.coRagEnabled
          ? {
              co_rag_agent_counts: { Semantic: 4, Keyword: 3, Conceptual: 5 },
              co_rag_total_before_merge: 12,
              co_rag_total_after_merge: 4,
              co_rag_merge_strategy: options.coRagMergeStrategy || "voting",
            }
          : null,
      },
    };
    // return axiosClient.post("/api/smartdoc/chat", { question, ...options });
  },

  // GET /api/smartdoc/chat/history
  getChatHistory: async () => {
    await mockDelay(200);
    return { data: mockHistory };
    // return axiosClient.get("/api/smartdoc/chat/history");
  },

  // DELETE /api/smartdoc/chat/history
  clearChatHistory: async () => {
    await mockDelay(300);
    mockHistory.length = 0;
    return { data: { success: true } };
    // return axiosClient.delete("/api/smartdoc/chat/history");
  },
};
