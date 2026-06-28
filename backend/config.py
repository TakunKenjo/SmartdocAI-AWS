import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Lambda chỉ cho phép ghi vào /tmp
# Nếu chạy local (không phải Lambda), dùng thư mục trong project
IS_LAMBDA = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

if IS_LAMBDA:
    UPLOAD_DIR = "/tmp/data/uploads"
    VECTORSTORE_DIR = "/tmp/vectorstore"
    # Trỏ HuggingFace cache đến model đã được pre-download trong image
    os.environ.setdefault("TRANSFORMERS_CACHE", "/var/task/hf_cache")
    os.environ.setdefault("HF_HOME", "/var/task/hf_cache")
else:
    UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
    VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

OLLAMA_MODEL = "qwen2.5:1.5b"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_TOP_P = 0.9
OLLAMA_REPEAT_PENALTY = 1.1
OLLAMA_NUM_CTX = 4096

AWS_MODEL_ID = "mistral.mixtral-8x7b-instruct-v0:1"
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# S3 Storage
S3_BUCKET = os.getenv("S3_BUCKET", "smartdocai-storage-623035187993")
S3_VECTORSTORE_PREFIX = "vectorstore"
S3_METADATA_PREFIX = "metadata"
S3_UPLOADS_PREFIX = "uploads"

# S3 keys cho metadata
S3_KEY_PROCESSED_FILES = f"{S3_METADATA_PREFIX}/processed_files.json"
S3_KEY_CHAT_HISTORY = f"{S3_METADATA_PREFIX}/chat_history.json"
S3_KEY_SEARCH_CONFIG = f"{S3_METADATA_PREFIX}/search_config.json"

EMBEDDING_MODEL = "sentence-transformers/LaBSE"
EMBEDDING_DEVICE = "cpu"
EMBEDDING_NORMALIZE = True

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

RETRIEVAL_SEARCH_TYPE = "mmr"
RETRIEVAL_TOP_K = 6
RETRIEVAL_FETCH_K = 30
RETRIEVAL_LAMBDA_MULT = 0.7

FAISS_INDEX_NAME = "smartdoc_index"

HYBRID_VECTOR_WEIGHT = 0.6
HYBRID_BM25_WEIGHT   = 0.4
HYBRID_TOP_K         = 3

METADATA_FILTER_FIELD = "source"

CO_RAG_TOP_K_PER_AGENT = 5
CO_RAG_MIN_VOTES = 2
CO_RAG_MERGE_STRATEGY = "voting"
