/**
 * CoRagMetadata — Panel hiển thị Co-RAG Analysis sau câu trả lời
 */
function CoRagMetadata({ meta }) {
  if (!meta) return null;

  const {
    co_rag_agent_counts = {},
    co_rag_total_before_merge = 0,
    co_rag_total_after_merge = 0,
    co_rag_merge_strategy = "voting",
  } = meta;

  const strategyColor =
    co_rag_merge_strategy === "voting"
      ? "text-blue-600 dark:text-blue-400"
      : co_rag_merge_strategy === "union"
        ? "text-emerald-600 dark:text-emerald-400"
        : "text-amber-600 dark:text-amber-400";

  return (
    <div className="bg-blue-50/60 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-3 text-xs space-y-2 w-full">
      <p className="text-[10px] font-bold text-blue-400 dark:text-blue-500 uppercase tracking-widest">
        Co-RAG Analysis
      </p>

      {/* Agent counts */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-slate-600 dark:text-slate-400">
        {Object.entries(co_rag_agent_counts).map(([name, cnt]) => (
          <span key={name}>
            <span className="text-blue-500">●</span>{" "}
            <strong>{name}</strong>: {cnt} docs
          </span>
        ))}
      </div>

      {/* Merge stats */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-slate-400 dark:text-slate-500">
        <span>
          Tổng docs (trước merge):{" "}
          <strong className="text-slate-600 dark:text-slate-400">{co_rag_total_before_merge}</strong>
        </span>
        <span>
          Sau Consensus Merger:{" "}
          <strong className="text-slate-600 dark:text-slate-400">{co_rag_total_after_merge}</strong>
        </span>
        <span>
          Chiến lược:{" "}
          <strong className={strategyColor}>{co_rag_merge_strategy}</strong>
        </span>
      </div>
    </div>
  );
}

export default CoRagMetadata;
