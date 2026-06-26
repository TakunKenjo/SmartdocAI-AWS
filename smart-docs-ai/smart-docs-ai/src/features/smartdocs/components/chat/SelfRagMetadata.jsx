import { cn } from "@/lib/utils";

/**
 * SelfRagMetadata — Panel hiển thị thông tin Self-RAG Analysis sau câu trả lời
 */
function SelfRagMetadata({ meta }) {
  if (!meta) return null;

  const {
    confidence_score = 0.5,
    is_grounded = true,
    has_hallucination = false,
    grading_feedback = "",
    rewritten_queries = [],
    docs_before_filter = 0,
    docs_after_filter = 0,
    sub_questions = [],
    used_multihop = false,
  } = meta;

  const confPct = Math.round(confidence_score * 100);
  const confLabel = confPct >= 70 ? "Cao" : confPct >= 40 ? "Trung bình" : "Thấp";
  const confColor =
    confPct >= 70
      ? "text-emerald-600 dark:text-emerald-400"
      : confPct >= 40
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-600 dark:text-red-400";
  const confBg =
    confPct >= 70
      ? "bg-emerald-50 dark:bg-emerald-900/20"
      : confPct >= 40
        ? "bg-amber-50 dark:bg-amber-900/20"
        : "bg-red-50 dark:bg-red-900/20";

  return (
    <div className="bg-blue-50/60 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-3 text-xs space-y-2 w-full">
      <p className="text-[10px] font-bold text-blue-400 dark:text-blue-500 uppercase tracking-widest">
        Self-RAG Analysis
      </p>

      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        {/* Confidence */}
        <span className={cn("font-semibold", confColor)}>
          Confidence:{" "}
          <span className={cn("px-1.5 py-0.5 rounded-md text-[10px]", confBg, confColor)}>
            {confPct}% ({confLabel})
          </span>
        </span>

        {/* Grounded */}
        <span className={is_grounded ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}>
          {is_grounded ? "✓ Dựa trên tài liệu" : "⚠ Có thể tự bịa"}
        </span>

        {/* Hallucination */}
        <span className={has_hallucination ? "text-red-600 dark:text-red-400" : "text-slate-500 dark:text-slate-400"}>
          {has_hallucination ? "⚠ Có thể có hallucination" : "✓ Không phát hiện hallucination"}
        </span>
      </div>

      {grading_feedback && (
        <p className="text-slate-500 dark:text-slate-400 italic">{grading_feedback}</p>
      )}

      <p className="text-slate-400 dark:text-slate-500">
        Docs: {docs_before_filter} retrieved → {docs_after_filter} sau filter
        {used_multihop && sub_questions.length > 0 ? ` | Multi-hop: ${sub_questions.length} sub-questions` : ""}
      </p>

      {/* Rewritten queries */}
      {rewritten_queries.length > 1 && (
        <details className="cursor-pointer">
          <summary className="text-blue-500 dark:text-blue-400 font-semibold hover:text-blue-700 dark:hover:text-blue-300 list-none flex items-center gap-1">
            <span className="text-[10px]">▶</span> Xem Query Rewriting
          </summary>
          <ul className="mt-1.5 space-y-0.5 pl-3">
            {rewritten_queries.map((q, i) => (
              <li key={i} className="text-slate-600 dark:text-slate-400">
                <span className="font-semibold">{i === 0 ? "Gốc" : `Variant ${i}`}:</span> {q}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export default SelfRagMetadata;
