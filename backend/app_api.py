import os
import sys

# Thiết lập biến môi trường Hugging Face để trỏ đến model được tải sẵn trong image
os.environ["HF_HOME"] = "/var/task/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/var/task/hf_cache"
os.environ["HF_HUB_OFFLINE"] = "1"


import json
import logging
import tempfile
import time
import shutil
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from mangum import Mangum

# Thêm root directory vào path để import các modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
CROSS_ENCODER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
from modules import s3_storage

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("SmartDocAI_API")


app = FastAPI(
    title="SmartDocAI API",
    version="1.0.0",
    root_path="/prod"  # API Gateway stage prefix
)

# Cấu hình CORS để hỗ trợ React chạy trên môi trường dev local khác port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thư mục lưu trữ
_PERSIST_DIR = config.VECTORSTORE_DIR
_FILES_PATH = os.path.join(_PERSIST_DIR, "processed_files.json")
_HISTORY_PATH = os.path.join(_PERSIST_DIR, "chat_history.json")
_CONFIG_PATH = os.path.join(_PERSIST_DIR, "search_config.json")

# Trạng thái trong bộ nhớ (Global State)
state = {
    "vector_store": None,
    "processed_files": [],
    "total_chunks": 0,
    "raw_documents": [],
    "chat_history": [],
    "llm_status": None,
    
    # Settings mặc định
    "chunk_size": config.CHUNK_SIZE,
    "chunk_overlap": config.CHUNK_OVERLAP,
    "hybrid_enabled": False,
    "reranker_enabled": False,
    "self_rag_enabled": False,
    "self_rag_query_rewrite": True,
    "self_rag_relevance_filter": True,
    "self_rag_answer_grading": True,
    "co_rag_enabled": False,
    "co_rag_agent_semantic": True,
    "co_rag_agent_keyword": True,
    "co_rag_agent_conceptual": True,
    "co_rag_merge_strategy": "voting",
    "active_file_filter": []
}

# --- PERSISTENCE HELPERS ---

def save_processed_files(files_info: list, user_id: str = None):
    """Lưu danh sách file đã xử lý riêng per-user"""
    if config.IS_LAMBDA:
        # Per-user processed files in S3
        if user_id:
            key = f"processed_files/{user_id}.json"
        else:
            key = config.S3_KEY_PROCESSED_FILES
        s3_storage.save_json(files_info, key)
    else:
        try:
            os.makedirs(_PERSIST_DIR, exist_ok=True)
            # Per-user processed files in local filesystem
            if user_id:
                path = os.path.join(_PERSIST_DIR, f"processed_files_{user_id}.json")
            else:
                path = _FILES_PATH
            with open(path, "w", encoding="utf-8") as f:
                json.dump(files_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu processed_files: {e}")

def load_processed_files(user_id: str = None) -> list:
    """Tải danh sách file đã xử lý riêng per-user"""
    if config.IS_LAMBDA:
        # Per-user processed files from S3
        if user_id:
            key = f"processed_files/{user_id}.json"
        else:
            key = config.S3_KEY_PROCESSED_FILES
        return s3_storage.load_json(key, default=[])
    
    # Per-user processed files from local filesystem
    if user_id:
        path = os.path.join(_PERSIST_DIR, f"processed_files_{user_id}.json")
    else:
        path = _FILES_PATH
    
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Lỗi khi tải processed_files: {e}")
        return []

def save_chat_history(history: list, user_id: str = None):
    """Lưu chat history riêng per-user"""
    safe_history = []
    for msg in history:
        safe_msg = {
            "role": msg.get("role", ""),
            "content": msg.get("content", ""),
            "sources": msg.get("sources", []),
            "question_ctx": msg.get("question_ctx", ""),
            "answer_ctx": msg.get("answer_ctx", ""),
            "self_rag_meta": msg.get("self_rag_meta"),
            "co_rag_meta": msg.get("co_rag_meta"),
            "timestamp": msg.get("timestamp", time.time())
        }
        safe_history.append(safe_msg)

    if config.IS_LAMBDA:
        # Per-user chat history in S3
        if user_id:
            key = f"chat_history/{user_id}.json"
        else:
            key = config.S3_KEY_CHAT_HISTORY
        s3_storage.save_json(safe_history, key)
    else:
        try:
            os.makedirs(_PERSIST_DIR, exist_ok=True)
            # Per-user chat history in local filesystem
            if user_id:
                path = os.path.join(_PERSIST_DIR, f"chat_history_{user_id}.json")
            else:
                path = _HISTORY_PATH
            with open(path, "w", encoding="utf-8") as f:
                json.dump(safe_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu chat_history: {e}")

def load_chat_history(user_id: str = None) -> list:
    """Tải chat history riêng per-user"""
    if config.IS_LAMBDA:
        # Per-user chat history from S3
        if user_id:
            key = f"chat_history/{user_id}.json"
        else:
            key = config.S3_KEY_CHAT_HISTORY
        return s3_storage.load_json(key, default=[])
    
    # Per-user chat history from local filesystem
    if user_id:
        path = os.path.join(_PERSIST_DIR, f"chat_history_{user_id}.json")
    else:
        path = _HISTORY_PATH
    
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Lỗi khi tải chat_history: {e}")
        return []

def save_app_config():
    config_data = {
        "chunk_size": state["chunk_size"],
        "chunk_overlap": state["chunk_overlap"],
        "hybrid_enabled": state["hybrid_enabled"],
        "reranker_enabled": state["reranker_enabled"],
        "self_rag_enabled": state["self_rag_enabled"],
        "self_rag_query_rewrite": state["self_rag_query_rewrite"],
        "self_rag_relevance_filter": state["self_rag_relevance_filter"],
        "self_rag_answer_grading": state["self_rag_answer_grading"],
        "co_rag_enabled": state["co_rag_enabled"],
        "co_rag_agent_semantic": state["co_rag_agent_semantic"],
        "co_rag_agent_keyword": state["co_rag_agent_keyword"],
        "co_rag_agent_conceptual": state["co_rag_agent_conceptual"],
        "co_rag_merge_strategy": state["co_rag_merge_strategy"],
        "active_file_filter": state["active_file_filter"]
    }
    if config.IS_LAMBDA:
        s3_storage.save_json(config_data, config.S3_KEY_SEARCH_CONFIG)
    else:
        try:
            os.makedirs(_PERSIST_DIR, exist_ok=True)
            with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi khi lưu config: {e}")

def load_app_config():
    if config.IS_LAMBDA:
        config_data = s3_storage.load_json(config.S3_KEY_SEARCH_CONFIG, default={})
    else:
        if not os.path.exists(_CONFIG_PATH):
            return
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi tải config: {e}")
            return
    for k, v in config_data.items():
        if k in state:
            state[k] = v

# --- INIT STATE ---

_config_loaded = False
_files_loaded = False
_history_loaded = False


def get_app_config():
    global _config_loaded
    if not _config_loaded or config.IS_LAMBDA:
        load_app_config()
        _config_loaded = True


def get_processed_files(user_id: str = None):
    """Lấy danh sách file đã xử lý riêng per-user - luôn tải mới từ storage (không cache global)"""
    saved_files = load_processed_files(user_id)
    if saved_files:
        total_chunks = sum(f.get("chunks", 0) for f in saved_files)
        logger.info(f"Khôi phục {len(saved_files)} file, {total_chunks} chunks cho user {user_id}")
        return saved_files
    return []


def get_chat_history(user_id: str = None):
    """Tải chat history per-user từ S3/disk"""
    # Always load from storage để đảm bảo per-user isolation
    saved_history = load_chat_history(user_id)
    if saved_history:
        state["chat_history"] = saved_history
        logger.info(f"Đã khôi phục {len(saved_history)} tin nhắn cho user {user_id or 'unknown'}.")
    else:
        state["chat_history"] = []
    return state["chat_history"]


def get_vector_store(user_id: str = None) -> Optional[Any]:
    """Get vector store - per-user. Rebuilds from user's documents each request"""
    # Load user's processed files
    latest_files = get_processed_files(user_id)
    
    if not latest_files:
        return None
    
    # For per-user isolation: rebuild vector store from user's documents each time
    # This ensures User A's documents don't leak to User B's queries
    try:
        from modules.vector_store import load_vector_store
        from modules.document_processor import Document
        
        # Load all user's documents from S3/disk
        raw_docs = []
        for file_info in latest_files:
            s3_key = file_info.get("s3_key")
            if s3_key:
                # Load document chunks from storage
                # Since we don't have per-user document storage yet,
                # we'll need to rebuild from uploaded files
                pass
        
        # For MVP: rebuild from cache if available, else load from S3
        logger.info(f"Loading vector store for user {user_id}...")
        saved_store = load_vector_store(force_download=False)
        
        if saved_store is not None:
            logger.info(f"Loaded vector store with {len(latest_files)} files for user {user_id}")
            return saved_store
        else:
            logger.warning(f"No vector store found for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error loading vector store for user {user_id}: {e}")
        return None


@app.on_event("startup")
def startup_event():
    logger.info("Khởi động API server SmartDocAI...")

# --- UTILITIES ---

def scan_docs_by_question_numbers(query: str, raw_documents: list) -> list:
    import re as _re
    if not raw_documents:
        return []

    STRUCT_KEYWORDS = [
        'câu', 'chương', 'mục', 'tiểu mục', 'phần', 'bài', 'đề', 'ví dụ',
        'chapter', 'section', 'part', 'exercise', 'question',
    ]
    patterns_to_search = []

    range_pat = _re.compile(
        r'(' + '|'.join(STRUCT_KEYWORDS) + r')\s+([\d\.]+)\s*(?:đến|tới|to|-)\s*([\d\.]+)',
        _re.IGNORECASE
    )
    for m in range_pat.finditer(query):
        keyword = m.group(1)
        try:
            start, end = int(float(m.group(2))), int(float(m.group(3)))
            for n in range(start, end + 1):
                patterns_to_search.append(_re.compile(
                    rf'(?:{_re.escape(keyword)}\s+{n}\b)',
                    _re.IGNORECASE
                ))
        except ValueError:
            pass

    single_pat = _re.compile(
        r'(' + '|'.join(STRUCT_KEYWORDS) + r')\s+([\dIVXivx\.]+[a-zA-Z]?)',
        _re.IGNORECASE
    )
    for m in single_pat.finditer(query):
        keyword, val = m.group(1), m.group(2)
        patterns_to_search.append(_re.compile(
            rf'(?:{_re.escape(keyword)}\s+{_re.escape(val)}\b)',
            _re.IGNORECASE
        ))

    if not patterns_to_search:
        return []

    matched = []
    seen = set()
    for doc in raw_documents:
        text = doc.page_content
        for pat in patterns_to_search:
            if pat.search(text):
                key = text[:120]
                if key not in seen:
                    seen.add(key)
                    matched.append(doc)
                break

    return matched[:10]

# --- REQUEST SCHEMAS ---

class ConfigUpdate(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    hybrid_enabled: Optional[bool] = None
    reranker_enabled: Optional[bool] = None
    self_rag_enabled: Optional[bool] = None
    self_rag_query_rewrite: Optional[bool] = None
    self_rag_relevance_filter: Optional[bool] = None
    self_rag_answer_grading: Optional[bool] = None
    co_rag_enabled: Optional[bool] = None
    co_rag_agent_semantic: Optional[bool] = None
    co_rag_agent_keyword: Optional[bool] = None
    co_rag_agent_conceptual: Optional[bool] = None
    co_rag_merge_strategy: Optional[str] = None
    active_file_filter: Optional[List[str]] = None

class ChatRequest(BaseModel):
    message: str
    hybridEnabled: Optional[bool] = None
    rerankerEnabled: Optional[bool] = None
    selfRagEnabled: Optional[bool] = None
    selfRagQueryRewrite: Optional[bool] = None
    selfRagRelevanceFilter: Optional[bool] = None
    selfRagAnswerGrading: Optional[bool] = None
    coRagEnabled: Optional[bool] = None
    coRagMergeStrategy: Optional[str] = None
    coRagAgentSemantic: Optional[bool] = None
    coRagAgentKeyword: Optional[bool] = None
    coRagAgentConceptual: Optional[bool] = None
    activeFileFilter: Optional[List[str]] = None

class UploadUrlRequest(BaseModel):
    filename: str
    content_type: Optional[str] = "application/octet-stream"

class ProcessDocumentRequest(BaseModel):
    filename: str
    s3_key: str
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

class DeleteDocumentRequest(BaseModel):
    filename: str


@app.get("/api/status")
def get_status(authorization: str = Header(None)):
    """Get status - shows per-user file counts"""
    from modules.rag_chain import check_aws_connection

    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass

    connection = check_aws_connection()
    state["llm_status"] = connection
    processed_files = get_processed_files(user_id)

    return {
         "online": connection,

        "provider": config.LLM_PROVIDER,
        "model": config.AWS_MODEL_ID,

        "embedding_provider": config.EMBEDDING_PROVIDER,
        "embedding_model": config.EMBEDDING_MODEL,

        "total_files": len(processed_files),
        "total_pages": sum(f.get("pages", 0) for f in processed_files),
        "total_chunks": sum(f.get("chunks", 0) for f in processed_files),

        "model_ready": True
    }



@app.get("/api/config")
def get_config():
    get_app_config()
    return {
        "chunk_size": state["chunk_size"],
        "chunk_overlap": state["chunk_overlap"],
        "hybrid_enabled": state["hybrid_enabled"],
        "reranker_enabled": state["reranker_enabled"],
        "self_rag_enabled": state["self_rag_enabled"],
        "self_rag_query_rewrite": state["self_rag_query_rewrite"],
        "self_rag_relevance_filter": state["self_rag_relevance_filter"],
        "self_rag_answer_grading": state["self_rag_answer_grading"],
        "co_rag_enabled": state["co_rag_enabled"],
        "co_rag_agent_semantic": state["co_rag_agent_semantic"],
        "co_rag_agent_keyword": state["co_rag_agent_keyword"],
        "co_rag_agent_conceptual": state["co_rag_agent_conceptual"],
        "co_rag_merge_strategy": state["co_rag_merge_strategy"],
        "active_file_filter": state["active_file_filter"]
    }


@app.post("/api/config")
def update_config(data: ConfigUpdate):
    get_app_config()
    for key, value in data.dict(exclude_unset=True).items():
        if key in state:
            state[key] = value
    save_app_config()
    return {"status": "success", "config": get_config()}


@app.get("/api/files")
def get_files(authorization: str = Header(None)):
    """Get user's documents - per-user"""
    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass
    return get_processed_files(user_id)

@app.post("/api/upload-url")
def get_upload_url(data: UploadUrlRequest):
    if not data.filename:
        raise HTTPException(status_code=400, detail="Filename là bắt buộc.")
    
    clean_filename = os.path.basename(data.filename)
    s3_key = f"uploads/{clean_filename}"
    upload_url = s3_storage.generate_presigned_upload_url(s3_key, data.content_type)
    
    if not upload_url:
        raise HTTPException(status_code=500, detail="Không thể tạo presigned URL từ S3.")
        
    return {
        "status": "success",
        "upload_url": upload_url,
        "s3_key": s3_key,
        "filename": clean_filename
    }


@app.post("/api/process")
def process_document(data: ProcessDocumentRequest, authorization: str = Header(None)):
    """Process document - per-user"""
    from modules.vector_store import create_vector_store, save_vector_store, create_bm25_retriever
    from modules.document_processor import extract_text_from_pdf, extract_text_from_docx, split_documents

    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass

    if not data.filename or not data.s3_key:
        raise HTTPException(status_code=400, detail="Filename và s3_key là bắt buộc.")

    if data.chunk_size is not None:
        state["chunk_size"] = data.chunk_size
    if data.chunk_overlap is not None:
        state["chunk_overlap"] = data.chunk_overlap

    file_ext = os.path.splitext(data.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Định dạng {file_ext} không được hỗ trợ.")

    local_file_path = os.path.join(tempfile.gettempdir(), "uploads", data.filename)
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

    if config.IS_LAMBDA or not os.path.exists(local_file_path):
        success = s3_storage.download_file(data.s3_key, local_file_path)
        if not success:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy file {data.s3_key} trên S3.")

    # Tải danh sách file và vector store hiện tại trước khi xử lý để thêm/ghi đè tài liệu mới
    get_processed_files(user_id)
    get_vector_store(user_id)

    # Kiểm tra nếu file đã tồn tại, xóa dữ liệu cũ của file đó trước để tránh bị trùng lặp khi ghi đè
    state["processed_files"] = [f for f in state["processed_files"] if f["name"] != data.filename]
    state["raw_documents"] = [doc for doc in state["raw_documents"] if doc.metadata.get("source") != data.filename]

    global _files_loaded
    _files_loaded = True

    if file_ext == ".docx":
        raw_docs = extract_text_from_docx(local_file_path, source_name=data.filename)
    else:
        raw_docs = extract_text_from_pdf(local_file_path, source_name=data.filename)

    if not raw_docs:
        raise HTTPException(status_code=400, detail=f"File {data.filename} không chứa chữ.")

    file_chunks = split_documents(
        raw_docs,
        chunk_size=state["chunk_size"],
        chunk_overlap=state["chunk_overlap"]
    )

    if file_chunks:
        # Add user_id to document metadata for per-user isolation
        for doc in file_chunks:
            if not doc.metadata:
                doc.metadata = {}
            doc.metadata["user_id"] = user_id or "global"
        
        state["raw_documents"].extend(file_chunks)
        state["processed_files"].append({
            "name": data.filename,
            "chunks": len(file_chunks),
            "pages": len(raw_docs),
            "s3_key": data.s3_key
        })
        state["total_chunks"] = sum(f.get("chunks", 0) for f in state["processed_files"])

        vector_store = create_vector_store(state["raw_documents"])
        state["vector_store"] = vector_store
        save_vector_store(vector_store)

        if state["hybrid_enabled"]:
            create_bm25_retriever(state["raw_documents"])

        save_processed_files(state["processed_files"], user_id)

    return {
        "status": "success",
        "processed_files": state["processed_files"],
        "total_chunks": state["total_chunks"]
    }


@app.post("/api/delete-document")
def delete_document(data: DeleteDocumentRequest, authorization: str = Header(None)):
    """Delete user's document - per-user"""
    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass
    
    filename = data.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename là bắt buộc.")

    # 1. Tải danh sách file và vector store hiện tại
    processed_files = get_processed_files(user_id)
    get_vector_store(user_id)

    # 2. Định vị file tương ứng để lấy s3_key
    target_file = None
    for f in processed_files:
        if f["name"] == filename:
            target_file = f
            break

    if not target_file:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy tài liệu {filename}")

    # 3. Xóa đối tượng trên S3 (ở thư mục uploads)
    s3_key = target_file.get("s3_key")
    if s3_key:
        try:
            s3_storage.delete_key(s3_key)
        except Exception as e:
            logger.error(f"Lỗi khi xóa file {s3_key} trên S3: {e}")

    # 4. Xóa file local tạm (nếu có)
    local_file_path = os.path.join(tempfile.gettempdir(), "uploads", filename)
    if os.path.exists(local_file_path):
        try:
            os.remove(local_file_path)
        except Exception as e:
            logger.error(f"Lỗi khi xóa local file {local_file_path}: {e}")

    # 5. Loại bỏ các chunks liên quan trong state["raw_documents"] và cập nhật processed_files
    state["processed_files"] = [f for f in processed_files if f["name"] != filename]
    state["raw_documents"] = [doc for doc in state["raw_documents"] if doc.metadata.get("source") != filename]
    state["total_chunks"] = sum(f.get("chunks", 0) for f in state["processed_files"])

    # 6. Cập nhật lại Vector Store
    if state["raw_documents"]:
        from modules.vector_store import create_vector_store, save_vector_store, create_bm25_retriever
        new_vs = create_vector_store(state["raw_documents"])
        state["vector_store"] = new_vs
        save_vector_store(new_vs)
        if state["hybrid_enabled"]:
            create_bm25_retriever(state["raw_documents"])
    else:
        from modules.vector_store import clear_vector_store
        clear_vector_store()
        state["vector_store"] = None

    # 7. Lưu lại processed_files.json
    save_processed_files(state["processed_files"], user_id)

    # 8. Cập nhật active_file_filter nếu file bị xóa đang nằm trong bộ lọc
    get_app_config()
    if filename in state["active_file_filter"]:
        state["active_file_filter"] = [name for name in state["active_file_filter"] if name != filename]
        save_app_config()

    return {
        "status": "success",
        "processed_files": state["processed_files"],
        "total_chunks": state["total_chunks"]
    }




@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, authorization: str = Header(None)):
    """Chat endpoint - per-user isolation"""
    
    # Extract user_id from JWT token (for per-user chat isolation)
    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            # If token invalid, continue without user isolation
            pass
    
    user_input = request.message
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="Nội dung tin nhắn trống.")

    # Cập nhật cài đặt động từ client nếu được gửi lên
    if request.hybridEnabled is not None: state["hybrid_enabled"] = request.hybridEnabled
    if request.rerankerEnabled is not None: state["reranker_enabled"] = request.rerankerEnabled
    if request.selfRagEnabled is not None: state["self_rag_enabled"] = request.selfRagEnabled
    if request.selfRagQueryRewrite is not None: state["self_rag_query_rewrite"] = request.selfRagQueryRewrite
    if request.selfRagRelevanceFilter is not None: state["self_rag_relevance_filter"] = request.selfRagRelevanceFilter
    if request.selfRagAnswerGrading is not None: state["self_rag_answer_grading"] = request.selfRagAnswerGrading
    if request.coRagEnabled is not None: state["co_rag_enabled"] = request.coRagEnabled
    if request.coRagMergeStrategy is not None: state["co_rag_merge_strategy"] = request.coRagMergeStrategy
    if request.coRagAgentSemantic is not None: state["co_rag_agent_semantic"] = request.coRagAgentSemantic
    if request.coRagAgentKeyword is not None: state["co_rag_agent_keyword"] = request.coRagAgentKeyword
    if request.coRagAgentConceptual is not None: state["co_rag_agent_conceptual"] = request.coRagAgentConceptual
    if request.activeFileFilter is not None: state["active_file_filter"] = request.activeFileFilter

    # Lưu câu hỏi của người dùng vào history (per-user isolation)
    chat_history = get_chat_history(user_id)
    user_msg = {"role": "user", "content": user_input, "timestamp": time.time()}
    chat_history.append(user_msg)
    save_chat_history(chat_history, user_id)

    # Bắt đầu xử lý phản hồi từ AI
    self_rag_meta = None
    co_rag_meta = None
    result = None

    try:
        from modules.rag_chain import ask_question, get_llm, _compute_rrf_scores
        from modules.self_rag import self_rag_pipeline
        from modules.co_rag import co_rag_pipeline
        from modules.vector_store import (
            create_bm25_retriever,
            create_ensemble_retriever,
            get_cached_bm25_retriever,
        )
        from modules.reranker import rerank_with_cross_encoder

        # Lấy vector store (tải per-user từ disk/S3 nếu chưa tải)
        vector_store = get_vector_store(user_id)
        
        # Filter raw_documents theo user_id để đảm bảo per-user isolation
        if user_id:
            user_documents = [
                doc for doc in state.get("raw_documents", [])
                if doc.metadata and doc.metadata.get("user_id") == user_id
            ]
        else:
            user_documents = state.get("raw_documents", [])
        
        # If no vector store but have user documents, need to rebuild
        if vector_store is None and user_documents:
            logger.warning(f"Vector store not found for user {user_id}, but have {len(user_documents)} documents. Rebuilding...")
            from modules.vector_store import create_vector_store
            try:
                vector_store = create_vector_store(user_documents)
            except Exception as e:
                logger.error(f"Error rebuilding vector store: {e}")
                vector_store = None
        
        # Use only user's documents for this chat (override state temporarily)
        original_raw_documents = state["raw_documents"]
        state["raw_documents"] = user_documents

        # 1. Pipeline: Self-RAG
        if state["self_rag_enabled"] and vector_store is not None:
            llm = get_llm()
            result = self_rag_pipeline(
                question=user_input,
                vector_store=vector_store,
                llm=llm,
                enable_query_rewrite=state["self_rag_query_rewrite"],
                enable_relevance_filter=state["self_rag_relevance_filter"],
                enable_answer_grading=state["self_rag_answer_grading"],
            )
            result["search_mode"] = "self_rag"
            result["active_filter"] = state["active_file_filter"]
            self_rag_meta = result

        # 2. Pipeline: Co-RAG (Multi-Agent)
        elif state["co_rag_enabled"] and vector_store is not None:
            llm = get_llm()
            result = co_rag_pipeline(
                question=user_input,
                vector_store=vector_store,
                raw_documents=state["raw_documents"],
                llm=llm,
                min_votes=config.CO_RAG_MIN_VOTES,
                merge_strategy=state["co_rag_merge_strategy"],
                enable_agent_semantic=state["co_rag_agent_semantic"],
                enable_agent_keyword=state["co_rag_agent_keyword"],
                enable_agent_conceptual=state["co_rag_agent_conceptual"],
            )
            result["search_mode"] = "co_rag"
            result["active_filter"] = state["active_file_filter"]
            co_rag_meta = result

        # 3. Pipeline: RAG chuẩn / Hybrid / Reranked
        else:
            retriever = None
            if state["hybrid_enabled"] and vector_store is not None:
                bm25 = get_cached_bm25_retriever()
                if bm25 is None and state["raw_documents"]:
                    bm25 = create_bm25_retriever(state["raw_documents"])
                if bm25 is not None:
                    retriever = create_ensemble_retriever(vector_store, bm25)

            forced_docs = scan_docs_by_question_numbers(
                user_input, state["raw_documents"]
            )

            result = ask_question(
                question=user_input,
                vector_store=vector_store,
                chat_history=chat_history,
                retriever=retriever,
                file_filter=state["active_file_filter"],
                forced_docs=forced_docs if forced_docs else None,
                raw_documents=state["raw_documents"],
                reranker_enabled=state["reranker_enabled"],
            )

            # Nếu bật Reranker, cập nhật search_mode để hiển thị trên UI
            if state["reranker_enabled"] and vector_store is not None:
                result["search_mode"] = result.get("search_mode", "vector") + "+reranked"

        # Định dạng cấu trúc trả về
        mode = result.get("search_mode", "vector")
        active_filter = result.get("active_filter", [])
        
        # Làm sạch sources để an toàn khi chuyển json
        sources_clean = []
        for s in result.get("sources", []):
            sources_clean.append({
                "file": s.get("file", ""),
                "page": s.get("page", "?"),
                "total_pages": s.get("total_pages"),
                "file_type": s.get("file_type", "pdf"),
                "content": s.get("content", ""),
                "chunk_index": s.get("chunk_index", ""),
                "score": float(s.get("score", 0.0))
            })

        # Chuẩn hóa Self-RAG Metadata sang JSON-serializable
        self_rag_data = None
        if self_rag_meta:
            self_rag_data = {
                "confidence_score": float(self_rag_meta.get("confidence_score", 0.5)),
                "is_grounded": bool(self_rag_meta.get("is_grounded", True)),
                "has_hallucination": bool(self_rag_meta.get("has_hallucination", False)),
                "grading_feedback": str(self_rag_meta.get("grading_feedback", "")),
                "rewritten_queries": self_rag_meta.get("rewritten_queries", []),
                "docs_before_filter": int(self_rag_meta.get("docs_before_filter", 0)),
                "docs_after_filter": int(self_rag_meta.get("docs_after_filter", 0)),
                "sub_questions": self_rag_meta.get("sub_questions", []),
                "used_multihop": bool(self_rag_meta.get("used_multihop", False))
            }

        # Chuẩn hóa Co-RAG Metadata
        co_rag_data = None
        if co_rag_meta:
            co_rag_data = {
                "co_rag_agent_counts": {str(k): int(v) for k, v in co_rag_meta.get("co_rag_agent_counts", {}).items()},
                "co_rag_total_before_merge": int(co_rag_meta.get("co_rag_total_before_merge", 0)),
                "co_rag_total_after_merge": int(co_rag_meta.get("co_rag_total_after_merge", 0)),
                "co_rag_merge_strategy": str(co_rag_meta.get("co_rag_merge_strategy", "voting"))
            }

        assistant_msg = {
            "role": "assistant",
            "content": result.get("answer", ""),
            "answer": result.get("answer", ""), # Đối chiếu cho frontend
            "sources": sources_clean,
            "question_ctx": user_input,
            "question": user_input, # Đối chiếu cho frontend
            "answer_ctx": result.get("answer", ""),
            "self_rag_meta": self_rag_data,
            "co_rag_meta": co_rag_data,
            "timestamp": time.time(),
            "search_mode": mode,
            "active_filter": active_filter,
            "error": result.get("error"),
            "used_fallback": result.get("used_fallback", False)
        }

        chat_history.append(assistant_msg)
        save_chat_history(chat_history, user_id)
        
        # Restore original raw_documents for next request
        state["raw_documents"] = original_raw_documents

        return assistant_msg

    except Exception as e:
        logger.error(f"Lỗi trong endpoint chat: {e}", exc_info=True)
        # Rollback message của user nếu lỗi để tránh mất đồng bộ
        chat_history = get_chat_history(user_id)
        if chat_history and chat_history[-1]["role"] == "user":
            chat_history.pop()
            save_chat_history(chat_history, user_id)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý câu hỏi: {str(e)}")
    finally:
        # Restore original raw_documents
        if 'original_raw_documents' in locals():
            state["raw_documents"] = original_raw_documents

@app.get("/api/history")
def get_history(authorization: str = Header(None)):
    """Get chat history - per-user"""
    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass
    return get_chat_history(user_id)


@app.post("/api/clear-history")
def clear_history(authorization: str = Header(None)):
    """Clear user's chat history - per-user"""
    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass
    
    state["chat_history"] = []
    
    # Xóa local copy
    try:
        if user_id:
            path = os.path.join(_PERSIST_DIR, f"chat_history_{user_id}.json")
        else:
            path = _HISTORY_PATH
        
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Lỗi khi xóa chat_history local: {e}")
        
    # Xóa trên S3 để đồng bộ hóa serverless
    if config.IS_LAMBDA:
        try:
            if user_id:
                key = f"chat_history/{user_id}.json"
            else:
                key = config.S3_KEY_CHAT_HISTORY
            s3_storage.delete_key(key)
        except Exception as e:
            logger.error(f"Lỗi khi xóa chat_history trên S3: {e}")
            raise HTTPException(status_code=500, detail=f"Không thể xóa file lịch sử trên S3: {e}")
            
    return {"status": "success"}


@app.post("/api/clear-documents")
def clear_documents(authorization: str = Header(None)):
    """Clear user's documents - per-user"""
    from modules.vector_store import clear_vector_store
    
    user_id = None
    if authorization:
        try:
            user_id = extract_user_id_from_token(authorization)
        except HTTPException:
            pass
    
    clear_vector_store()
    
    # Xóa file persist local (per-user)
    if user_id:
        local_file_path = os.path.join(_PERSIST_DIR, f"processed_files_{user_id}.json")
    else:
        local_file_path = _FILES_PATH
    
    try:
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
    except Exception as e:
        logger.error(f"Lỗi khi xóa {local_file_path} local: {e}")

    # Xóa file persist trên S3 để đồng bộ hóa serverless (per-user)
    if config.IS_LAMBDA:
        if user_id:
            s3_key = f"processed_files/{user_id}.json"
        else:
            s3_key = config.S3_KEY_PROCESSED_FILES
        
        try:
            s3_storage.delete_key(s3_key)
        except Exception as e:
            logger.error(f"Lỗi khi xóa {s3_key} trên S3: {e}")

    state["vector_store"] = None
    state["processed_files"] = []
    state["total_chunks"] = 0
    state["raw_documents"] = []
    state["active_file_filter"] = []
    
    return {"status": "success"}

# ════════════════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS — Xác thực người dùng (Register, Confirm)
# ════════════════════════════════════════════════════════════════════════════════

from modules import auth_service, profile_service
from fastapi import Header


# ─── Request Schemas (Auth) ────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Đăng ký tài khoản mới"""
    email: str
    password: str
    fullname: str
    phone: str
    dob: str  # YYYY-MM-DD


class ConfirmSignUpRequest(BaseModel):
    """Xác thực email đăng ký"""
    email: str
    confirmation_code: str


# ─── Endpoints (Auth) ──────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """
    POST /api/auth/register — Đăng ký tài khoản mới
    
    Tạo user mới trong Cognito + DynamoDB profile
    
    Request:
    {
        "email": "user@example.com",
        "password": "Password123!",
        "fullname": "Nguyễn Văn A",
        "phone": "0901234567",
        "dob": "1990-01-01"
    }
    
    Response:
    {
        "success": true,
        "user_id": "...",
        "email": "...",
        "message": "Đăng ký thành công..."
    }
    """
    try:
        logger.info(f"[Auth] Register: email={request.email}")
        result = auth_service.register_user(
            email=request.email,
            password=request.password,
            fullname=request.fullname,
            phone=request.phone,
            dob=request.dob
        )
        logger.info(f"[Auth] ✅ Register success: {result['user_id']}")
        return result
    
    except ValueError as e:
        logger.warning(f"[Auth] ⚠️  Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        error_msg = str(e).lower()
        # Duplicate email should return 409 Conflict
        if "đã được đăng ký" in error_msg or "already" in error_msg:
            logger.warning(f"[Auth] ⚠️  Duplicate email: {e}")
            raise HTTPException(status_code=409, detail=str(e))
        logger.error(f"[Auth] ❌ Register error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/confirm-signup")
async def confirm_signup(request: ConfirmSignUpRequest):
    """
    POST /api/auth/confirm-signup — Xác thực email đăng ký
    
    Xác nhận mã từ email để kích hoạt tài khoản
    
    Request:
    {
        "email": "user@example.com",
        "confirmation_code": "123456"
    }
    
    Response:
    {
        "success": true,
        "message": "Email xác thực thành công..."
    }
    """
    try:
        logger.info(f"[Auth] ConfirmSignUp: email={request.email}")
        result = auth_service.confirm_user_signup(
            email=request.email,
            confirmation_code=request.confirmation_code
        )
        logger.info(f"[Auth] ✅ ConfirmSignUp success: {request.email}")
        return result
    
    except Exception as e:
        logger.error(f"[Auth] ❌ ConfirmSignUp error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ════════════════════════════════════════════════════════════════════════════════
# PROFILE ENDPOINTS — Quản lý hồ sơ người dùng
# ════════════════════════════════════════════════════════════════════════════════

def extract_user_id_from_token(authorization: str = Header(None)) -> str:
    """
    Trích xuất user_id (Cognito sub) từ JWT token Authorization header
    Header format: "Bearer eyJhbGc..."
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    
    try:
        import json
        import base64
        
        token = authorization.replace("Bearer ", "").strip()
        parts = token.split(".")
        
        if len(parts) != 3:
            raise ValueError("Token format không hợp lệ")
        
        # Decode JWT payload
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        
        user_id = claims.get("sub")
        if not user_id:
            raise ValueError("Token không chứa 'sub' claim")
        
        return user_id
        
    except Exception as e:
        logger.error(f"[Token] Lỗi decode: {e}")
        raise HTTPException(status_code=401, detail=f"Token không hợp lệ: {str(e)}")


# ─── Request Schemas ───────────────────────────────────────────────────────

class PersonalInfoRequest(BaseModel):
    """Cập nhật thông tin cá nhân"""
    fullname: str
    email: str
    phone: str
    dob: str  # YYYY-MM-DD


class AvatarRequest(BaseModel):
    """Upload avatar"""
    avatar: str  # base64 string


class ChangePasswordRequest(BaseModel):
    """Đổi mật khẩu"""
    current_password: str
    new_password: str


# ─── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/profile")
def get_profile(authorization: str = Header(None)):
    """GET /api/profile — Lấy hồ sơ người dùng"""
    try:
        user_id = extract_user_id_from_token(authorization)
        user_profile = profile_service.get_user_profile(user_id)
        
        if not user_profile:
            raise HTTPException(status_code=404, detail="Hồ sơ người dùng không tìm thấy")
        
        return user_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Profile] Lỗi: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@app.put("/api/profile/personal-info")
def update_personal_info(
    data: PersonalInfoRequest,
    authorization: str = Header(None)
):
    """PUT /api/profile/personal-info — Cập nhật info (name, email, phone, dob)"""
    try:
        user_id = extract_user_id_from_token(authorization)
        result = profile_service.update_personal_info(
            user_id=user_id,
            fullname=data.fullname,
            email=data.email,
            phone=data.phone,
            dob=data.dob
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Profile] Lỗi: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/profile/avatar")
def update_avatar(
    data: AvatarRequest,
    authorization: str = Header(None)
):
    """PUT /api/profile/avatar — Upload avatar"""
    try:
        user_id = extract_user_id_from_token(authorization)
        result = profile_service.update_avatar(user_id, data.avatar)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Profile] Lỗi: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/profile/change-password")
def change_password(
    data: ChangePasswordRequest,
    authorization: str = Header(None)
):
    """POST /api/profile/change-password — Đổi mật khẩu"""
    try:
        import json
        import base64
        
        # Extract email từ JWT token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        
        token = authorization.replace("Bearer ", "").strip()
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token format không hợp lệ")
        
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        
        user_id = claims.get("sub")
        email = claims.get("email")
        
        if not user_id:
            raise ValueError("Token không chứa 'sub' claim")
        
        result = profile_service.change_password(
            user_id=user_id,
            email=email,
            current_password=data.current_password,
            new_password=data.new_password
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Profile] Lỗi: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Phục vụ file tĩnh của frontend React ở root
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Wrapper handler cho AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_api.py:app", host="127.0.0.1", port=8000, reload=True)
