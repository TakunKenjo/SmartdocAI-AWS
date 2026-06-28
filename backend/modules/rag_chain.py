import os
import boto3
from dotenv import load_dotenv

load_dotenv() # Đọc mã bảo mật từ file .env

# Tạo kết nối đến AWS
if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    # Trên Lambda, sử dụng IAM Role của Lambda (smartdocai-lambda-role)
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
else:
    # Chạy local, sử dụng access keys từ .env
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
import logging
import re
from typing import Optional, Dict, Any, List

from langchain_core.documents import Document

from modules.vector_store import similarity_search, similarity_search_with_scores
from modules.language_detector import detect_language, get_language_instruction
import config

logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = """Bạn là SmartDocAI, một trợ lý AI thông minh chuyên phân tích và trả lời câu hỏi dựa trên nội dung tài liệu.

{language_instruction}

### QUY TẮC:
1. CHỈ trả lời dựa trên thông tin trong phần CONTEXT bên dưới.
2. Nếu CONTEXT không chứa đủ thông tin để trả lời, hãy nói rõ ràng thông tin không có trong tài liệu.
3. Trích dẫn nguồn (tên file, số trang) khi có thể.
4. Trả lời có cấu trúc, rõ ràng, dễ đọc.
5. Không bịa đặt thông tin ngoài CONTEXT.
6. Nếu câu hỏi liên quan đến lịch sử hội thoại, hãy tham chiếu các câu trả lời trước đó.

{chat_history_section}### CONTEXT:
{context}

### CÂU HỎI:
{question}

### TRẢ LỜI:"""


REFORMULATE_QUESTION_TEMPLATE = """Dựa vào lịch sử hội thoại bên dưới và câu hỏi tiếp theo của người dùng, hãy viết lại câu hỏi thành một câu hoàn chỉnh, độc lập (standalone question) để có thể tìm kiếm trong tài liệu mà không cần ngữ cảnh hội thoại.

Chỉ trả về câu hỏi đã viết lại, không giải thích thêm.

### LỊCH SỬ HỘI THOẠI:
{chat_history}

### CÂU HỎI TIẾP THEO:
{question}

### CÂU HỎI ĐÃ VIẾT LẠI:"""

NO_CONTEXT_PROMPT_TEMPLATE = """Bạn là SmartDocAI, một trợ lý AI thông minh.

{language_instruction}

Người dùng chưa tải tài liệu lên hệ thống. Hãy thông báo lịch sự rằng:
- Họ cần tải file PDF lên trước khi đặt câu hỏi.
- Hướng dẫn họ bấm nút "Tải tài liệu" ở phía trên để tải file lên.

### CÂU HỎI CỦA NGƯỜI DÙNG:
{question}

### TRẢ LỜI:"""


def _clean_source_name(source: str) -> str:
    name = os.path.basename(str(source or "N/A"))
    if re.match(r"^tmp[a-zA-Z0-9_\\-]+\\.pdf$", name):
        return "Tai lieu da tai len (du lieu cu)"
    return name


def _build_fallback_answer(relevant_docs: list[Document], language: str) -> str:
    if not relevant_docs:
        if language == "vi":
            return (
                "Mình chưa thể truy cập mô hình AI để sinh câu trả lời chi tiết. "
                "Hiện cũng không tìm thấy đoạn nội dung phù hợp trong tài liệu."
            )
        return (
            "I cannot reach the AI model right now, and no relevant document "
            "segments were found for this question."
        )

    snippets = []
    for idx, doc in enumerate(relevant_docs[:3], 1):
        source = _clean_source_name(doc.metadata.get("source", "N/A"))
        page = doc.metadata.get("page", "N/A")
        short_text = " ".join(doc.page_content.split())
        if len(short_text) > 260:
            short_text = f"{short_text[:260].rstrip()}..."
        snippets.append(f"{idx}. ({source} - Trang {page}) {short_text}")

    if language == "vi":
        intro = (
            "AWS Bedrock/LLM hiện chưa sẵn sàng, nên mình tạm gửi các đoạn liên quan nhất "
            "để bạn tham khảo nhanh:"
        )
    else:
        intro = (
            "The AWS Bedrock/LLM service is currently unavailable, so here are the most "
            "relevant document snippets for quick reference:"
        )

    return f"{intro}\n\n" + "\n\n".join(snippets)


_llm = None


def get_llm() -> Any:
    global _llm
    if _llm is None:
        from langchain_aws import ChatBedrock
        logger.info("Đang khởi tạo kết nối AWS Bedrock (Mixtral 8x7B)...")
        _llm = ChatBedrock(
            client=bedrock_client,
            model_id="mistral.mixtral-8x7b-instruct-v0:1", # type:ignore
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 4096,
                "top_p": 0.9
            }
        )
        logger.info("Đã kết nối AWS Bedrock thành công!")
    return _llm


def check_ollama_connection() -> bool:
    try:
        # Kiểm tra nhanh cấu hình AWS
        has_keys = bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
        return has_keys
    except Exception:
        return False


def _reformulate_question(question: str, chat_history: list, llm: Any) -> str:
    if not chat_history:
        return question

    recent = [m for m in chat_history if m.get("role") in ("user", "assistant")][-6:]
    if not recent:
        return question

    history_text = ""
    for msg in recent:
        role_label = "Người dùng" if msg["role"] == "user" else "Trợ lý"
        history_text += f"{role_label}: {msg['content']}\n"

    try:
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_template(REFORMULATE_QUESTION_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({"chat_history": history_text, "question": question})
        reformulated = response.content.strip()
        if reformulated:
            logger.info(f"Reformulated: '{question}' -> '{reformulated}'")
            return reformulated
    except Exception as e:
        logger.warning(f"Không thể reformulate question: {e}")

    return question


def format_context(documents: list[Document]) -> str:
    if not documents:
        return "Không tìm thấy thông tin liên quan trong tài liệu."

    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = _clean_source_name(doc.metadata.get("source", "N/A"))
        page = doc.metadata.get("page", "N/A")
        context_parts.append(
            f"[Nguồn {i}: {source} - Trang {page}]\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)


def _compute_rrf_scores(retriever, query: str, k: int = 60) -> list:
    sub_retrievers = getattr(retriever, "retrievers", None)
    weights = getattr(retriever, "weights", None)

    if not sub_retrievers:
        raw_docs = retriever.invoke(query)
        return [(doc, round(1.0 - i / max(len(raw_docs), 1), 2)) for i, doc in enumerate(raw_docs)]

    if weights is None:
        weights = [1.0 / len(sub_retrievers)] * len(sub_retrievers)

    all_ranked = []
    for sub_ret in sub_retrievers:
        try:
            docs = sub_ret.invoke(query)
        except Exception:
            docs = []
        all_ranked.append(docs)

    doc_rrf: dict = {}
    for docs, weight in zip(all_ranked, weights):
        for rank, doc in enumerate(docs, start=1):
            key = doc.page_content[:100]
            rrf_contrib = weight / (k + rank)
            if key not in doc_rrf:
                doc_rrf[key] = [doc, 0.0]
            doc_rrf[key][1] += rrf_contrib

    rrf_theoretical_max = sum(weights) / (k + 1)
    sorted_pairs = sorted(doc_rrf.values(), key=lambda x: -x[1])
    return [
        (doc, round(min(1.0, score / rrf_theoretical_max), 4))
        for doc, score in sorted_pairs
    ]


def ask_question(
    question: str,
    vector_store=None,
    chat_history: Optional[list] = None,
    retriever=None,
    file_filter: Optional[list] = None,
    forced_docs: Optional[list] = None,
) -> Dict[str, Any]:
    result = {
        "answer": "",
        "sources": [],
        "language": "en",
        "error": None,
        "used_fallback": False,
    }

    if not question or not str(question).strip():
        result["answer"] = (
            "Vui lòng nhập câu hỏi của bạn trước khi gửi."
            if detect_language(question or "") == "vi"
            else "Please enter your question before submitting."
        )
        result["error"] = "empty_question"
        return result

    question = str(question).strip()

    try:
        from langchain_core.prompts import ChatPromptTemplate
        language = detect_language(question)
        result["language"] = language
        llm = get_llm()
        chat_history_section = ""
        if chat_history:
            recent_history = [m for m in chat_history if m.get("role") in ("user", "assistant")][-6:]
            if recent_history:
                lines = []
                for msg in recent_history:
                    role_label = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                    lines.append(f"{role_label}: {msg['content']}")
                chat_history_section = "### LỊCH SỬ HỘI THOẠI:\n" + "\n".join(lines) + "\n\n"

        if vector_store is None:
            prompt = ChatPromptTemplate.from_template(NO_CONTEXT_PROMPT_TEMPLATE)
            language_instruction = get_language_instruction(language) 
            chain = prompt | llm
            response = chain.invoke({
                "question": question,
                "language_instruction": language_instruction,
            })
            result["answer"] = response.content
        else:
            search_question = _reformulate_question(question, chat_history, llm)
            if retriever is not None:
                doc_score_pairs = _compute_rrf_scores(retriever, search_question)
            else:
                doc_score_pairs = similarity_search_with_scores(vector_store, search_question)

            if forced_docs:
                existing_keys = {d.page_content[:120] for d, _ in doc_score_pairs}
                injected = [
                    (doc, 1.0) for doc in forced_docs
                    if doc.page_content[:120] not in existing_keys
                ]
                if injected:
                    logger.info(f"Injected {len(injected)} forced docs by question number scan.")
                doc_score_pairs = injected + list(doc_score_pairs)

            if file_filter:
                doc_score_pairs = [
                    (doc, score) for doc, score in doc_score_pairs
                    if any(f in doc.metadata.get("source", "") for f in file_filter)
                ]
            relevant_docs = [doc for doc, _ in doc_score_pairs]
            context = format_context(relevant_docs)

            language_instruction = get_language_instruction(language)
            prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
            effective_question = question
            if forced_docs:
                range_match = re.search(
                    r'(câu|chương|mục|tiểu mục|phần|bài|chapter|section|part)'
                    r'\s+([\d\.]+)\s*(?:đến|tới|to|-)\s*([\d\.]+)',
                    question, re.IGNORECASE
                )
                if range_match:
                    kw = range_match.group(1)
                    start_n = range_match.group(2)
                    end_n = range_match.group(3)
                    effective_question = (
                        question +
                        f"\n[Yêu cầu bắt buộc: Hãy đề cập đến TẤT CẢ {kw} từ {start_n} đến {end_n}. "
                        f"Không được bỏ sót bất kỳ {kw} nào trong khoảng này.]"
                    )
                    logger.info(f"Coverage hint injected for {kw} {start_n}-{end_n}")

            chain = prompt | llm
            response = chain.invoke({
                "question": effective_question,
                "context": context,
                "language_instruction": language_instruction,
                "chat_history_section": chat_history_section,
            })

            result["answer"] = response.content

            seen_keys = set()
            sources = []
            for chunk_idx, (doc, score) in enumerate(doc_score_pairs):
                file_name = _clean_source_name(doc.metadata.get("source", "N/A"))
                page = doc.metadata.get("page", "N/A")
                dedup_key = (file_name, page, doc.page_content[:80])
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                sources.append({
                    "file": file_name,
                    "page": page,
                    "total_pages": doc.metadata.get("total_pages"),
                    "file_type": doc.metadata.get("file_type", "pdf"),
                    "content": doc.page_content,
                    "chunk_index": chunk_idx + 1,
                    "score": round(float(score), 3),
                })
            result["sources"] = sources
            result["search_mode"] = "hybrid" if retriever is not None else "vector"
            result["active_filter"] = file_filter or []

    except Exception as e:
        error_msg = f"Lỗi xử lý: {str(e)}"
        result["error"] = error_msg
        logger.error(error_msg)
        
        if vector_store is not None:
            doc_score_pairs = similarity_search_with_scores(vector_store, question)
            relevant_docs = [doc for doc, _ in doc_score_pairs]
            result["answer"] = _build_fallback_answer(relevant_docs, result["language"])
            result["used_fallback"] = True
            seen_keys = set()
            sources = []
            for chunk_idx, (doc, score) in enumerate(doc_score_pairs):
                file_name = _clean_source_name(doc.metadata.get("source", "N/A"))
                page = doc.metadata.get("page", "N/A")
                dedup_key = (file_name, page, doc.page_content[:80])
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                sources.append({
                    "file": file_name,
                    "page": page,
                    "total_pages": doc.metadata.get("total_pages"),
                    "file_type": doc.metadata.get("file_type", "pdf"),
                    "content": doc.page_content,
                    "chunk_index": chunk_idx + 1,
                    "score": round(float(score), 3),
                })
            result["sources"] = sources
            result["search_mode"] = "hybrid" if retriever is not None else "vector"
            result["active_filter"] = file_filter or []
    return result
