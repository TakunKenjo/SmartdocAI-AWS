import os
import logging
import shutil
from typing import List, Optional

from langchain_core.documents import Document
from typing import Any

import config
from modules import s3_storage

logger = logging.getLogger(__name__)

# Cache embedding model để tránh tải lại nhiều lần
_embedding_model = None


def get_embedding_model() -> Any:
    global _embedding_model

    if _embedding_model is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        logger.info(f"Đang tải embedding model: {config.EMBEDDING_MODEL}...")
        logger.info("Nếu đây là lần đầu, quá trình tải có thể mất vài phút (~470 MB).")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={"device": config.EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Đã tải embedding model thành công!")

    return _embedding_model


def create_vector_store(documents: List[Document]) -> Optional[Any]:
    if not documents:
        logger.warning("Không có documents để tạo vector store.")
        return None

    try:
        from langchain_community.vectorstores import FAISS
        embeddings = get_embedding_model()
        logger.info(f"Đang tạo vector store từ {len(documents)} chunks...")
        vector_store = FAISS.from_documents(documents, embeddings)
        logger.info("Đã tạo vector store thành công!")
        return vector_store

    except Exception as e:
        logger.error(f"Lỗi khi tạo vector store: {str(e)}")
        raise Exception(
            f"Không thể tạo vector store. Chi tiết: {str(e)}"
        )


def save_vector_store(vector_store: Any, index_name: Optional[str] = None):
    _index_name = index_name or config.FAISS_INDEX_NAME
    save_path = os.path.join(config.VECTORSTORE_DIR, _index_name)

    try:
        # Lưu FAISS index xuống /tmp
        vector_store.save_local(save_path)
        logger.info(f"Đã lưu vector store local tại: {save_path}")

        # Sync lên S3
        if config.IS_LAMBDA:
            s3_storage.upload_vectorstore(save_path, _index_name)

    except Exception as e:
        logger.error(f"Lỗi khi lưu vector store: {str(e)}")
        raise


def load_vector_store(index_name: Optional[str] = None, force_download: bool = False) -> Optional[Any]:
    _index_name = index_name or config.FAISS_INDEX_NAME
    load_path = os.path.join(config.VECTORSTORE_DIR, _index_name)

    # Nếu chạy trên Lambda, tải từ S3 nếu chưa có local copy hoặc có yêu cầu force_download
    if config.IS_LAMBDA:
        if force_download or not os.path.exists(load_path):
            logger.info(f"Đang tải vector store từ S3 (force={force_download})...")
            if os.path.exists(load_path):
                try:
                    shutil.rmtree(load_path)
                except Exception as e:
                    logger.warning(f"Không thể xóa thư mục vector store local cũ: {e}")
            s3_storage.download_vectorstore(load_path, _index_name)

    if not os.path.exists(load_path):
        logger.info("Chưa có vector store được lưu trước đó.")
        return None

    try:
        from langchain_community.vectorstores import FAISS
        embeddings = get_embedding_model()
        vector_store = FAISS.load_local(
            load_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info(f"Đã tải vector store từ: {load_path}")
        return vector_store

    except Exception as e:
        logger.error(f"Lỗi khi tải vector store: {str(e)}")
        return None


def add_documents_to_store(
    vector_store: Any, documents: List[Document]
) -> Any:
    if not documents:
        return vector_store

    try:
        from langchain_community.vectorstores import FAISS
        embeddings = get_embedding_model()
        new_store = FAISS.from_documents(documents, embeddings)
        vector_store.merge_from(new_store)
        logger.info(f"Đã thêm {len(documents)} chunks vào vector store.")
        return vector_store

    except Exception as e:
        logger.error(f"Lỗi khi thêm documents: {str(e)}")
        raise


def similarity_search(
    vector_store: Any, query: str, top_k: Optional[int] = None
) -> List[Document]:
    _top_k = top_k or config.RETRIEVAL_TOP_K
    _fetch_k = config.RETRIEVAL_FETCH_K
    _lambda_mult = config.RETRIEVAL_LAMBDA_MULT

    try:
        results = vector_store.max_marginal_relevance_search(
            query,
            k=_top_k,
            fetch_k=_fetch_k,
            lambda_mult=_lambda_mult,
        )

        logger.info(f"Tìm thấy {len(results)} kết quả (fetch_k={_fetch_k}) cho query: '{query[:50]}...'")
        return results

    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm: {str(e)}")
        return []


def similarity_search_with_scores(
    vector_store: Any, query: str, top_k: Optional[int] = None
) -> List[tuple]:
    """Trả về (Document, relevance_score) trong [0,1]."""
    _top_k = top_k or config.RETRIEVAL_TOP_K

    try:
        results = vector_store.similarity_search_with_relevance_scores(
            query,
            k=_top_k,
        )
        logger.info(
            f"[with_scores] Tìm thấy {len(results)} kết quả cho query: '{query[:50]}...'"
        )
        return results  # list of (Document, float)

    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm với score: {str(e)}")
        # Fallback: dùng MMR không có score, gán score = 0.0
        docs = similarity_search(vector_store, query, top_k)
        return [(doc, 0.0) for doc in docs]


def clear_vector_store(index_name: Optional[str] = None) -> bool:
    _index_name = index_name or config.FAISS_INDEX_NAME
    load_path = os.path.join(config.VECTORSTORE_DIR, _index_name)
    try:
        # Xóa local
        if os.path.exists(load_path):
            shutil.rmtree(load_path)
            logger.info(f"Đã xóa vector store local: {load_path}")

        # Xóa trên S3
        if config.IS_LAMBDA:
            s3_storage.delete_vectorstore(_index_name)

        return True
    except Exception as e:
        logger.error(f"Lỗi khi xóa vector store: {str(e)}")
        return False

_bm25_retriever_cache = None

def create_bm25_retriever(documents: List[Document], top_k: Optional[int] = None):
    global _bm25_retriever_cache
    try:
        from langchain_community.retrievers import BM25Retriever
        _k = top_k or config.HYBRID_TOP_K
        retriever = BM25Retriever.from_documents(documents)
        retriever.k = _k
        _bm25_retriever_cache = retriever
        logger.info(f"Đã tạo BM25 retriever với {len(documents)} documents, k={_k}")
        return retriever
    except Exception as e:
        logger.error(f"Lỗi khi tạo BM25 retriever: {str(e)}")
        return None


def get_cached_bm25_retriever():
    return _bm25_retriever_cache


def create_ensemble_retriever(vector_store: Any, bm25_retriever):
    try:
        from langchain_classic.retrievers import EnsembleRetriever
        faiss_retriever = vector_store.as_retriever(
            search_type=config.RETRIEVAL_SEARCH_TYPE,
            search_kwargs={
                "k": config.HYBRID_TOP_K,
                "fetch_k": config.RETRIEVAL_FETCH_K,
                "lambda_mult": config.RETRIEVAL_LAMBDA_MULT,
            },
        )
        ensemble = EnsembleRetriever(
            retrievers=[faiss_retriever, bm25_retriever],
            weights=[config.HYBRID_VECTOR_WEIGHT, config.HYBRID_BM25_WEIGHT],
        )
        logger.info("Đã tạo EnsembleRetriever (FAISS + BM25)")
        return ensemble
    except Exception as e:
        logger.error(f"Lỗi khi tạo EnsembleRetriever: {str(e)}")
        return None