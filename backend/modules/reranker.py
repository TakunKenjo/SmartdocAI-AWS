import logging
import time
from typing import List, Tuple, Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Cache cross-encoder model
_cross_encoder_model = None
CROSS_ENCODER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

def get_cross_encoder():
    """Singleton: tải cross-encoder model một lần duy nhất."""
    global _cross_encoder_model
    if _cross_encoder_model is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Đang tải Cross-Encoder: {CROSS_ENCODER_MODEL}...")
            _cross_encoder_model = CrossEncoder(CROSS_ENCODER_MODEL)
            logger.info("Đã tải Cross-Encoder thành công!")
        except Exception as e:
            logger.error(f"Lỗi tải Cross-Encoder: {e}")
            return None
    return _cross_encoder_model

def rerank_with_cross_encoder(
    query: str,
    doc_score_pairs: List[Tuple[Document, float]],
    top_k: int = 3,
) -> List[Tuple[Document, float, float]]:
    if not doc_score_pairs:
        return []

    cross_encoder = get_cross_encoder()
    if cross_encoder is None:
        # Fallback: trả về kết quả gốc với cross_score = bi_score
        logger.warning("Cross-Encoder không khả dụng, dùng bi-encoder scores.")
        return [
            (doc, score, score)
            for doc, score in doc_score_pairs[:top_k]
        ]

    try:
        t0 = time.perf_counter()

        # Tạo pairs (query, passage) cho cross-encoder
        pairs = [(query, doc.page_content) for doc, _ in doc_score_pairs]

        # Predict relevance scores
        cross_scores = cross_encoder.predict(pairs)

        # Normalize cross scores về [0, 1] bằng sigmoid
        # import math
        # min_s = float(min(cross_scores))
        # max_s = float(max(cross_scores))
        # normalized_scores = [round((float(s) - min_s) / (max_s - min_s + 1e-9), 4) for s in cross_scores]
        import math
        def sigmoid(x):
            return 1 / (1 + math.exp(-x))
        normalized_scores = [round(sigmoid(float(s)), 4) for s in cross_scores]

        # Kết hợp và sort theo cross-encoder score
        results = [
            (doc, bi_score, ce_score)
            for (doc, bi_score), ce_score
            in zip(doc_score_pairs, normalized_scores)
        ]
        results.sort(key=lambda x: x[2], reverse=True)

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.info(
            f"Cross-Encoder reranked {len(results)} docs → top {top_k} "
            f"(latency={latency_ms}ms)"
        )

        return results[:top_k]

    except Exception as e:
        logger.error(f"Lỗi khi rerank: {e}")
        return [
            (doc, score, score)
            for doc, score in doc_score_pairs[:top_k]
        ]

def compare_bi_vs_cross_encoder(
    query: str,
    doc_score_pairs: List[Tuple[Document, float]],
    top_k: int = 3,
) -> dict:
    """
    So sánh kết quả bi-encoder vs cross-encoder để hiển thị UI.

    Returns:
        dict với:
          - bi_encoder_results: [(doc, score)] theo thứ tự bi-encoder
          - cross_encoder_results: [(doc, bi_score, ce_score)] theo thứ tự cross-encoder
          - ranking_changed: True nếu thứ tự thay đổi
          - latency_ms: thời gian rerank
    """
    if not doc_score_pairs:
        return {
            "bi_encoder_results": [],
            "cross_encoder_results": [],
            "ranking_changed": False,
            "latency_ms": 0,
        }

    # Bi-encoder order (original)
    bi_results = doc_score_pairs[:top_k]

    # Cross-encoder rerank
    t0 = time.perf_counter()
    ce_results = rerank_with_cross_encoder(query, doc_score_pairs, top_k)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Kiểm tra thứ tự có thay đổi không
    bi_order = [id(doc) for doc, _ in bi_results]
    ce_order = [id(doc) for doc, _, _ in ce_results]
    ranking_changed = bi_order != ce_order

    return {
        "bi_encoder_results": bi_results,
        "cross_encoder_results": ce_results,
        "ranking_changed": ranking_changed,
        "latency_ms": latency_ms,
    }