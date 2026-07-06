

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from langchain_core.documents import Document
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate

import config

logger = logging.getLogger(__name__)



CO_RAG_DECOMPOSE_TEMPLATE = """Bạn là chuyên gia phân tích câu hỏi phức tạp.

Hãy phân rã câu hỏi sau thành TỐI ĐA 3 câu hỏi con đơn giản hơn để tìm kiếm thông tin.
Mỗi câu hỏi con nên hỏi về một khía cạnh cụ thể của câu hỏi gốc.

Chỉ trả về các câu hỏi con, mỗi câu một dòng, bắt đầu bằng số thứ tự.
Không giải thích thêm. Nếu câu hỏi đã đủ đơn giản, chỉ trả về chính câu hỏi đó.

Câu hỏi gốc: {question}

Các câu hỏi con:"""



def semantic_retriever_agent(
    query: str,
    vector_store,
    top_k: int = 5,
) -> List[Tuple[Document, float]]:

    try:
        results = vector_store.similarity_search_with_relevance_scores(
            query,
            k=top_k,
        )
        logger.info(f"[Co-RAG Agent1/Semantic] Truy xuất {len(results)} docs cho: '{query[:50]}'")
        return results
    except Exception as e:
        logger.warning(f"[Co-RAG Agent1/Semantic] Lỗi: {e}")
        return []



def keyword_retriever_agent(
    query: str,
    raw_documents: List[Document],
    top_k: int = 5,
) -> List[Tuple[Document, float]]:

    if not raw_documents:
        logger.warning("[Co-RAG Agent2/Keyword] Không có documents để xây BM25 index.")
        return []

    try:
        from langchain_community.retrievers import BM25Retriever

        retriever = BM25Retriever.from_documents(raw_documents)
        retriever.k = top_k
        docs = retriever.invoke(query)

        _rrf_k = 60
        _rrf_max = 1.0 / (_rrf_k + 1)
        results = []
        for i, doc in enumerate(docs):
            rrf_score = 1.0 / (_rrf_k + (i + 1))
            approx_score = round(rrf_score / _rrf_max, 4)
            results.append((doc, approx_score))

        logger.info(f"[Co-RAG Agent2/Keyword] Truy xuất {len(results)} docs cho: '{query[:50]}'")
        return results

    except Exception as e:
        logger.warning(f"[Co-RAG Agent2/Keyword] Lỗi: {e}")
        return []



def conceptual_decomposer_agent(
    question: str,
    vector_store,
    llm: ChatBedrock,
    top_k: int = 5,
) -> List[Tuple[Document, float]]:


    sub_questions = [question]
    try:
        prompt = ChatPromptTemplate.from_template(CO_RAG_DECOMPOSE_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({"question": question})
        raw = response.content.strip()

        parsed = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if cleaned and len(cleaned) > 5:
                parsed.append(cleaned)

        if parsed:
            sub_questions = parsed[:3]

        logger.info(f"[Co-RAG Agent3/Conceptual] Phân rã thành {len(sub_questions)} sub-questions")

    except Exception as e:
        logger.warning(f"[Co-RAG Agent3/Conceptual] Phân rã câu hỏi thất bại: {e}. Dùng câu gốc.")


    seen_content_keys = set()
    all_results: List[Tuple[Document, float]] = []

    for sub_q in sub_questions:
        try:
            results = vector_store.similarity_search_with_relevance_scores(
                sub_q,
                k=top_k,
            )
            for doc, score in results:
                key = doc.page_content[:120]
                if key not in seen_content_keys:
                    seen_content_keys.add(key)
                    all_results.append((doc, score))
        except Exception as e:
            logger.warning(f"[Co-RAG Agent3/Conceptual] Lỗi retrieve sub-question '{sub_q[:40]}': {e}")

    logger.info(f"[Co-RAG Agent3/Conceptual] Tổng {len(all_results)} docs (sau dedup)")
    return all_results



RRF_K = 60

def consensus_merger(
    agent_results: Dict[str, List[Tuple[Document, float]]],
    strategy: str = "voting",
    min_votes: int = 2,
) -> List[Tuple[Document, float, int]]:

    rrf_scores: Dict[str, float] = {}
    vote_counts: Dict[str, int] = {}
    representative_docs: Dict[str, Document] = {}

    for agent_name, results in agent_results.items():
        for rank_index, (doc, _score) in enumerate(results):
            rank = rank_index + 1
            rrf_contribution = 1.0 / (RRF_K + rank)

            fp = doc.page_content[:120]

            rrf_scores[fp] = rrf_scores.get(fp, 0.0) + rrf_contribution
            vote_counts[fp] = vote_counts.get(fp, 0) + 1
            if fp not in representative_docs:
                representative_docs[fp] = doc

    num_agents = len(agent_results)
    merged: List[Tuple[Document, float, int]] = []

    for fp in rrf_scores:
        vote_count = vote_counts[fp]
        rrf_score = rrf_scores[fp]

        vote_boost = 1.0 + (vote_count - 1) * 0.15
        merged_score = round(rrf_score * vote_boost, 6)

        if strategy == "voting" and vote_count < min_votes:
            continue
        elif strategy == "intersection" and vote_count < num_agents:
            continue

        merged.append((representative_docs[fp], merged_score, vote_count))

    merged.sort(key=lambda x: x[1], reverse=True)
    logger.info(
        f"[Co-RAG Merger/RRF] Strategy='{strategy}', "
        f"Total unique docs: {len(rrf_scores)} → Sau filter: {len(merged)}"
    )
    return merged



def co_rag_pipeline(
    question: str,
    vector_store,
    raw_documents: List[Document],
    llm: ChatBedrock,
    top_k_per_agent: Optional[int] = None,
    min_votes: Optional[int] = None,
    merge_strategy: Optional[str] = None,
    enable_agent_semantic: bool = True,
    enable_agent_keyword: bool = True,
    enable_agent_conceptual: bool = True,
) -> Dict[str, Any]:

    from modules.rag_chain import format_context, RAG_PROMPT_TEMPLATE
    from modules.language_detector import detect_language, get_language_instruction

    _top_k = top_k_per_agent or config.CO_RAG_TOP_K_PER_AGENT
    _min_votes = min_votes or config.CO_RAG_MIN_VOTES
    _strategy = merge_strategy or config.CO_RAG_MERGE_STRATEGY

    result: Dict[str, Any] = {
        "answer": "",
        "sources": [],
        "language": "vi",
        "error": None,
        "co_rag_agent_counts": {},
        "co_rag_total_before_merge": 0,
        "co_rag_total_after_merge": 0,
        "co_rag_merge_strategy": _strategy,
        "co_rag_sub_questions": [],
    }

    try:
        language = detect_language(question)
        result["language"] = language

        agent_results: Dict[str, List[Tuple[Document, float]]] = {}

        if enable_agent_semantic and vector_store is not None:
            agent1 = semantic_retriever_agent(question, vector_store, top_k=_top_k)
            agent_results["Semantic (FAISS)"] = agent1
            result["co_rag_agent_counts"]["Semantic (FAISS)"] = len(agent1)

        if enable_agent_keyword and raw_documents:
            agent2 = keyword_retriever_agent(question, raw_documents, top_k=_top_k)
            agent_results["Keyword (BM25)"] = agent2
            result["co_rag_agent_counts"]["Keyword (BM25)"] = len(agent2)

        if enable_agent_conceptual and vector_store is not None:
            agent3 = conceptual_decomposer_agent(question, vector_store, llm, top_k=_top_k)
            agent_results["Conceptual (LLM)"] = agent3
            result["co_rag_agent_counts"]["Conceptual (LLM)"] = len(agent3)

        if not agent_results:
            result["error"] = "Không có agent nào được kích hoạt hoặc không có dữ liệu."
            result["answer"] = "Không thể xử lý câu hỏi do chưa có tài liệu hoặc cấu hình sai."
            return result

        total_before = sum(len(v) for v in agent_results.values())
        result["co_rag_total_before_merge"] = total_before

        merged_docs_with_votes = consensus_merger(
            agent_results,
            strategy=_strategy,
            min_votes=_min_votes,
        )

        result["co_rag_total_after_merge"] = len(merged_docs_with_votes)

        if not merged_docs_with_votes:
            logger.warning("[Co-RAG] Voting cho 0 docs, fallback sang union top docs.")
            merged_docs_with_votes = consensus_merger(
                agent_results,
                strategy="union",
                min_votes=1,
            )

        top_merged = merged_docs_with_votes[:config.RETRIEVAL_TOP_K]

        docs_for_context = [doc for doc, _, _ in top_merged]
        context_text = format_context(docs_for_context)

        language_instruction = get_language_instruction(language)
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        chain = prompt | llm
        response = chain.invoke({
            "question": question,
            "context": context_text,
            "language_instruction": language_instruction,
            "chat_history_section": "",
        })
        result["answer"] = response.content

        import os as _os

        def _clean(s: str) -> str:
            return _os.path.basename(str(s or "N/A"))

        seen_keys = set()
        sources = []
        for idx, (doc, merged_score, vote_count) in enumerate(top_merged):
            fname = _clean(doc.metadata.get("source", "N/A"))
            page = doc.metadata.get("page", "N/A")
            dedup_key = (fname, page, doc.page_content[:80])
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            sources.append({
                "file": fname,
                "page": page,
                "total_pages": doc.metadata.get("total_pages"),
                "file_type": doc.metadata.get("file_type", "pdf"),
                "content": doc.page_content,
                "chunk_index": idx + 1,
                "score": merged_score,
                "vote_count": vote_count,
            })
        result["sources"] = sources

        logger.info(
            f"[Co-RAG] Hoàn thành: {len(agent_results)} agents, "
            f"{total_before} docs → {len(merged_docs_with_votes)} sau merge → "
            f"{len(sources)} nguồn cuối"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[Co-RAG] Pipeline lỗi: {e}")

    return result
