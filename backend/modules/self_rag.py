"""
SmartDocAI - Self-RAG (Q10)
LLM tự đánh giá câu trả lời, query rewriting, multi-hop reasoning,
confidence scoring.
"""

import logging
import re
from typing import Optional, List, Dict, Any

from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

import config

logger = logging.getLogger(__name__)

# ============================================================
# Prompt Templates
# ============================================================

QUERY_REWRITE_TEMPLATE = """Bạn là chuyên gia tối ưu hóa câu truy vấn tìm kiếm.

Hãy viết lại câu hỏi sau thành 3 phiên bản khác nhau để tìm kiếm tài liệu hiệu quả hơn.
Mỗi phiên bản nên tiếp cận từ góc độ khác nhau.

Chỉ trả về 3 câu hỏi, mỗi câu một dòng, bắt đầu bằng số thứ tự (1. 2. 3.).
Không giải thích thêm.

Câu hỏi gốc: {question}

3 câu hỏi viết lại:"""

RELEVANCE_CHECK_TEMPLATE = """Đánh giá xem đoạn văn bản sau có liên quan đến câu hỏi không.

Câu hỏi: {question}
Đoạn văn bản: {context}

Trả lời CHỈ bằng một từ: "CÓ" hoặc "KHÔNG"
Đánh giá:"""

ANSWER_GRADING_TEMPLATE = """Bạn là giám khảo đánh giá chất lượng câu trả lời AI.

Hãy đánh giá câu trả lời sau dựa trên:
1. Có trả lời đúng câu hỏi không?
2. Có dựa trên context được cung cấp không?
3. Có chứa thông tin bịa đặt không?

Câu hỏi: {question}
Context: {context}
Câu trả lời: {answer}

Trả về JSON với format sau (chỉ JSON, không giải thích):
{{"score": <0.0-1.0>, "is_grounded": <true/false>, "has_hallucination": <true/false>, "feedback": "<nhận xét ngắn>"}}

Đánh giá:"""

MULTIHOP_TEMPLATE = """Bạn là AI phân tích câu hỏi phức tạp cần nhiều bước suy luận.

Câu hỏi: {question}
Context hiện có: {context}

Hãy:
1. Xác định xem câu hỏi có cần thêm thông tin không
2. Nếu cần, đặt câu hỏi phụ để tìm kiếm thêm
3. Tổng hợp câu trả lời cuối cùng

Trả về JSON:
{{"needs_more_info": <true/false>, "sub_questions": ["<câu hỏi phụ 1>", ...], "final_answer": "<câu trả lời>"}}

Phân tích:"""

# ============================================================
# Query Rewriting
# ============================================================

def rewrite_query(question: str, llm: ChatBedrock) -> List[str]:
    """
    Tự động viết lại câu hỏi thành nhiều phiên bản để tăng recall.

    Args:
        question: Câu hỏi gốc
        llm: ChatBedrock instance

    Returns:
        List các câu hỏi đã viết lại (bao gồm câu gốc)
    """
    try:
        prompt = ChatPromptTemplate.from_template(QUERY_REWRITE_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({"question": question})
        raw = response.content.strip()

        # Parse các câu hỏi từ response
        lines = raw.split("\n")
        rewritten = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Loại bỏ prefix số thứ tự (1. 2. 3.)
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if cleaned and len(cleaned) > 10:
                rewritten.append(cleaned)

        # Giữ tối đa 3 câu, thêm câu gốc vào đầu
        rewritten = rewritten[:3]
        all_queries = [question] + [q for q in rewritten if q != question]

        logger.info(f"Query rewriting: '{question}' → {len(all_queries)} variants")
        return all_queries

    except Exception as e:
        logger.warning(f"Query rewriting thất bại: {e}")
        return [question]

# ============================================================
# Relevance Grading
# ============================================================

def grade_document_relevance(
    question: str,
    doc: Document,
    llm: ChatBedrock,
) -> bool:
    """
    LLM tự đánh giá xem document có liên quan đến câu hỏi không.

    Returns:
        True nếu liên quan, False nếu không
    """
    try:
        context_snippet = doc.page_content[:500]
        prompt = ChatPromptTemplate.from_template(RELEVANCE_CHECK_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({
            "question": question,
            "context": context_snippet,
        })
        answer = response.content.strip().upper()
        return "CÓ" in answer or "YES" in answer or "RELEVANT" in answer
    except Exception as e:
        logger.warning(f"Relevance check thất bại: {e}")
        return True  # Mặc định giữ lại document

def filter_relevant_docs(
    question: str,
    documents: List[Document],
    llm: ChatBedrock,
) -> List[Document]:
    """Lọc chỉ giữ các documents thực sự liên quan."""
    if not documents:
        return []

    relevant = []
    for doc in documents:
        if grade_document_relevance(question, doc, llm):
            relevant.append(doc)

    # Nếu lọc hết, trả về ít nhất top 2 ban đầu
    if not relevant and documents:
        logger.warning("Tất cả docs bị lọc, giữ lại 2 docs đầu tiên")
        return documents[:2]

    logger.info(f"Relevance filter: {len(documents)} → {len(relevant)} docs")
    return relevant

# ============================================================
# Answer Grading / Confidence Scoring
# ============================================================

def grade_answer(
    question: str,
    context: str,
    answer: str,
    llm: ChatBedrock,
) -> Dict[str, Any]:
    """
    LLM tự đánh giá chất lượng câu trả lời vừa sinh ra.

    Returns:
        dict với score, is_grounded, has_hallucination, feedback
    """
    default = {
        "score": 0.5,
        "is_grounded": True,
        "has_hallucination": False,
        "feedback": "Không thể đánh giá tự động.",
    }

    try:
        # Rút gọn context để tránh vượt token limit
        context_short = context[:800] if len(context) > 800 else context
        answer_short = answer[:600] if len(answer) > 600 else answer

        prompt = ChatPromptTemplate.from_template(ANSWER_GRADING_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({
            "question": question,
            "context": context_short,
            "answer": answer_short,
        })

        raw = response.content.strip()

        # Parse JSON
        import json
        # Tìm JSON trong response (đôi khi LLM thêm text thừa)
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "score": float(parsed.get("score", 0.5)),
                "is_grounded": bool(parsed.get("is_grounded", True)),
                "has_hallucination": bool(parsed.get("has_hallucination", False)),
                "feedback": str(parsed.get("feedback", "")),
            }

    except Exception as e:
        logger.warning(f"Answer grading thất bại: {e}")

    return default

# ============================================================
# Multi-hop Reasoning
# ============================================================

def multi_hop_reasoning(
    question: str,
    context: str,
    llm: ChatBedrock,
) -> Dict[str, Any]:
    """
    Kiểm tra xem câu hỏi có cần multi-hop reasoning không.
    Nếu cần, sinh câu hỏi phụ để tìm kiếm thêm thông tin.

    Returns:
        dict với needs_more_info, sub_questions, final_answer
    """
    default = {
        "needs_more_info": False,
        "sub_questions": [],
        "final_answer": "",
    }

    try:
        context_short = context[:600] if len(context) > 600 else context
        prompt = ChatPromptTemplate.from_template(MULTIHOP_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({
            "question": question,
            "context": context_short,
        })

        raw = response.content.strip()

        import json
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "needs_more_info": bool(parsed.get("needs_more_info", False)),
                "sub_questions": list(parsed.get("sub_questions", [])),
                "final_answer": str(parsed.get("final_answer", "")),
            }

    except Exception as e:
        logger.warning(f"Multi-hop reasoning thất bại: {e}")

    return default

# ============================================================
# Self-RAG Pipeline (orchestrator)
# ============================================================

def self_rag_pipeline(
    question: str,
    vector_store,
    llm: ChatBedrock,
    top_k: int = 5,
    enable_query_rewrite: bool = True,
    enable_relevance_filter: bool = True,
    enable_answer_grading: bool = True,
    file_filter: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Pipeline Self-RAG đầy đủ:
    1. Query rewriting → nhiều variants
    2. Retrieve với tất cả variants, dedup
    3. Relevance filtering
    4. Generate answer
    5. Answer grading + confidence score

    Args:
        question: Câu hỏi gốc
        vector_store: FAISS vector store
        llm: ChatBedrock instance
        top_k: Số kết quả mỗi lần retrieve
        enable_*: Bật/tắt từng bước
        file_filter: Danh sách filename để chỉ tìm kiếm trong các file đó (None/[] = tìm toàn bộ)

    Returns:
        dict đầy đủ kết quả Self-RAG
    """
    from modules.vector_store import similarity_search_with_scores
    from modules.rag_chain import format_context, RAG_PROMPT_TEMPLATE
    from modules.language_detector import detect_language, get_language_instruction

    result = {
        "answer": "",
        "sources": [],
        "language": "vi",
        "confidence_score": 0.5,
        "is_grounded": True,
        "has_hallucination": False,
        "grading_feedback": "",
        "rewritten_queries": [question],
        "docs_before_filter": 0,
        "docs_after_filter": 0,
        "sub_questions": [],
        "used_multihop": False,
        "error": None,
    }

    try:
        language = detect_language(question)
        result["language"] = language

        if enable_query_rewrite:
            all_queries = rewrite_query(question, llm)
        else:
            all_queries = [question]
        result["rewritten_queries"] = all_queries

        seen_contents = set()
        all_doc_score_pairs = []

        for q in all_queries:
            pairs = similarity_search_with_scores(vector_store, q, top_k=top_k)
            for doc, score in pairs:
                key = doc.page_content[:100]
                if key not in seen_contents:
                    seen_contents.add(key)
                    all_doc_score_pairs.append((doc, score))

        # Áp dụng file_filter ngay sau khi retrieve, trước relevance filtering
        if file_filter:
            all_doc_score_pairs = [
                (doc, score) for doc, score in all_doc_score_pairs
                if any(f in doc.metadata.get("source", "") for f in file_filter)
            ]

        all_docs = [doc for doc, _ in all_doc_score_pairs]
        result["docs_before_filter"] = len(all_docs)

        if enable_relevance_filter and all_docs:
            filtered_docs = filter_relevant_docs(question, all_docs, llm)
        else:
            filtered_docs = all_docs

        result["docs_after_filter"] = len(filtered_docs)

        context_text = format_context(filtered_docs[:top_k])
        multihop = multi_hop_reasoning(question, context_text, llm)
        result["sub_questions"] = multihop.get("sub_questions", [])

        # Nếu cần thêm thông tin, retrieve thêm với sub-questions
        if multihop.get("needs_more_info") and multihop.get("sub_questions"):
            result["used_multihop"] = True
            for sub_q in multihop["sub_questions"][:2]:
                extra_pairs = similarity_search_with_scores(vector_store, sub_q, top_k=2)
                if file_filter:
                    extra_pairs = [
                        (doc, score) for doc, score in extra_pairs
                        if any(f in doc.metadata.get("source", "") for f in file_filter)
                    ]
                for doc, score in extra_pairs:
                    key = doc.page_content[:100]
                    if key not in seen_contents:
                        seen_contents.add(key)
                        filtered_docs.append(doc)

            # Update context
            context_text = format_context(filtered_docs[:top_k + 2])

        language_instruction = get_language_instruction(language)
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({
            "question": question,
            "context": context_text,
            "language_instruction": language_instruction,
            "chat_history_section": "",
        })
        answer = response.content
        result["answer"] = answer

        if enable_answer_grading:
            grading = grade_answer(question, context_text, answer, llm)
            result["confidence_score"] = grading["score"]
            result["is_grounded"] = grading["is_grounded"]
            result["has_hallucination"] = grading["has_hallucination"]
            result["grading_feedback"] = grading["feedback"]

        import os as _os

        def clean_source(s):
            return _os.path.basename(str(s or "N/A"))

        # Build score lookup từ all_doc_score_pairs (key = 100 ký tự đầu content)
        score_map = {doc.page_content[:100]: score for doc, score in all_doc_score_pairs}

        seen_keys = set()
        sources = []
        for idx, doc in enumerate(filtered_docs[:top_k]):
            fname = clean_source(doc.metadata.get("source", "N/A"))
            page = doc.metadata.get("page", "N/A")
            key = (fname, page, doc.page_content[:80])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            sources.append({
                "file": fname,
                "page": page,
                "total_pages": doc.metadata.get("total_pages"),
                "file_type": doc.metadata.get("file_type", "pdf"),
                "content": doc.page_content,
                "chunk_index": idx + 1,
                "score": score_map.get(doc.page_content[:100], 0.0),
            })
        result["sources"] = sources

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Self-RAG pipeline lỗi: {e}")

    return result