import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Lambda chỉ cho phép ghi vào /tmp
# Nếu chạy local (không phải Lambda), dùng thư mục trong project
IS_LAMBDA = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

if IS_LAMBDA:
    UPLOAD_DIR = "/tmp/data/uploads"
    VECTORSTORE_DIR = "/tmp/vectorstore"
else:
    UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
    VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

AWS_MODEL_ID = "qwen.qwen3-next-80b-a3b"
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

# LLM
LLM_PROVIDER = "Amazon Bedrock"

# Embedding
EMBEDDING_PROVIDER = "Amazon Titan"
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIMENSIONS = 1024

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

RETRIEVAL_SEARCH_TYPE = "mmr"
RETRIEVAL_TOP_K = 10
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
