import { useDispatch, useSelector } from "react-redux";
import {
  selectHybridEnabled,
  selectRerankerEnabled,
  selectSelfRagEnabled,
  selectSelfRagConfig,
  selectCoRagEnabled,
  selectCoRagConfig,
  selectProcessedFiles,
  selectActiveFileFilter,
  setHybridEnabled,
  setRerankerEnabled,
  setSelfRagEnabled,
  setSelfRagConfig,
  setCoRagEnabled,
  setCoRagConfig,
  setActiveFileFilter,
} from "@/store/slices/smartdocSlice.js";
import { cn } from "@/lib/utils";

/**
 * SearchSettings — Panel cài đặt tìm kiếm nâng cao
 * Bao gồm: File Filter, Hybrid Search, Re-ranking, Self-RAG, Co-RAG
 * Layout 2 cột như Streamlit gốc
 */
function SearchSettings() {
  const dispatch = useDispatch();
  const hybridEnabled = useSelector(selectHybridEnabled);
  const rerankerEnabled = useSelector(selectRerankerEnabled);
  const selfRagEnabled = useSelector(selectSelfRagEnabled);
  const selfRagConfig = useSelector(selectSelfRagConfig);
  const coRagEnabled = useSelector(selectCoRagEnabled);
  const coRagConfig = useSelector(selectCoRagConfig);
  const files = useSelector(selectProcessedFiles);
  const activeFileFilter = useSelector(selectActiveFileFilter);

  const hasDocs = files.length > 0;
  const advancedModeOn = selfRagEnabled || coRagEnabled;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4">
      {/* ── Left Column ── */}
      <div className="space-y-4">
        {/* File Filter */}
        <div>
          <SectionLabel label="Lọc tài liệu" />
          {!hasDocs ? (
            <p className="text-[11px] text-slate-400 dark:text-slate-500 border border-dashed border-slate-200 dark:border-slate-700 rounded-lg p-2.5 text-center">
              Chưa có tài liệu để lọc.
            </p>
          ) : (
            <div className="space-y-1.5">
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                Chỉ tìm kiếm trong:
              </p>
              {files.map((f) => (
                <label
                  key={f.name}
                  className="flex items-center gap-2 cursor-pointer group"
                >
                  <input
                    type="checkbox"
                    checked={activeFileFilter.includes(f.name)}
                    onChange={(e) => {
                      const next = e.target.checked
                        ? [...activeFileFilter, f.name]
                        : activeFileFilter.filter((n) => n !== f.name);
                      dispatch(setActiveFileFilter(next));
                    }}
                    className="rounded border-slate-300 dark:border-slate-600 text-blue-600"
                  />
                  <span className="text-xs text-slate-700 dark:text-slate-300 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {f.name}
                  </span>
                </label>
              ))}
              <p className="text-[10px] text-slate-400 dark:text-slate-500">
                {activeFileFilter.length > 0
                  ? `Đang lọc: ${activeFileFilter.length}/${files.length} file`
                  : "Tìm kiếm toàn bộ tài liệu"}
              </p>
            </div>
          )}
        </div>

        {/* Hybrid Search */}
        <div>
          <SectionLabel label="Hybrid Search" />
          <ToggleRow
            id="hybrid-toggle"
            label="BM25 + Vector"
            checked={hybridEnabled && !advancedModeOn}
            disabled={!hasDocs || advancedModeOn}
            onChange={(v) => dispatch(setHybridEnabled(v))}
          />
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
            {!hasDocs
              ? "Tải tài liệu để kích hoạt"
              : advancedModeOn
                ? `⚠ Bị bypass bởi ${selfRagEnabled ? "Self-RAG" : "Co-RAG"}`
                : hybridEnabled
                  ? "Vector 60% + BM25 40%"
                  : "Pure Vector Search (FAISS)"}
          </p>
        </div>
      </div>

      {/* ── Right Column ── */}
      <div className="space-y-4">
        {/* Re-ranking */}
        <div>
          <SectionLabel label="Re-ranking" />
          <ToggleRow
            id="reranker-toggle"
            label="Cross-Encoder"
            checked={rerankerEnabled && !advancedModeOn}
            disabled={!hasDocs || advancedModeOn}
            onChange={(v) => dispatch(setRerankerEnabled(v))}
          />
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
            {!hasDocs
              ? "Tải tài liệu để kích hoạt"
              : advancedModeOn
                ? "⚠ Bị bypass — có cơ chế lọc riêng"
                : rerankerEnabled
                  ? "ms-marco-MiniLM-L-12-v2"
                  : "Dùng Bi-Encoder scores (FAISS)"}
          </p>
        </div>

        {/* Self-RAG */}
        <div>
          <SectionLabel label="Self-RAG" />
          <ToggleRow
            id="self-rag-toggle"
            label="AI tự đánh giá"
            checked={selfRagEnabled}
            disabled={!hasDocs}
            onChange={(v) => dispatch(setSelfRagEnabled(v))}
          />
          {selfRagEnabled && hasDocs && (
            <div className="mt-1.5 space-y-1 pl-2 border-l-2 border-blue-200 dark:border-blue-800">
              {[
                { key: "queryRewrite", label: "Query Rewriting" },
                { key: "relevanceFilter", label: "Relevance Filtering" },
                { key: "answerGrading", label: "Answer Grading" },
              ].map(({ key, label }) => (
                <CheckRow
                  key={key}
                  id={`self-rag-${key}`}
                  label={label}
                  checked={selfRagConfig[key]}
                  onChange={(v) => dispatch(setSelfRagConfig({ [key]: v }))}
                />
              ))}
            </div>
          )}
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
            {!hasDocs
              ? "Tải tài liệu để kích hoạt"
              : selfRagEnabled
                ? "Hybrid & Re-ranking bị bypass"
                : "Dùng RAG thông thường"}
          </p>
        </div>

        {/* Co-RAG */}
        <div>
          <SectionLabel label="Co-RAG (Multi-Agent)" />
          <ToggleRow
            id="co-rag-toggle"
            label="Multi-Agent RAG"
            checked={coRagEnabled}
            disabled={!hasDocs}
            onChange={(v) => dispatch(setCoRagEnabled(v))}
          />
          {coRagEnabled && hasDocs && (
            <div className="mt-1.5 space-y-1.5 pl-2 border-l-2 border-blue-200 dark:border-blue-800">
              <div>
                <label className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 block mb-1">
                  Chiến lược merge
                </label>
                <select
                  value={coRagConfig.strategy}
                  onChange={(e) => dispatch(setCoRagConfig({ strategy: e.target.value }))}
                  className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="voting">voting — ≥2 agents đồng ý</option>
                  <option value="union">union — giữ tất cả</option>
                  <option value="intersection">intersection — mọi agents</option>
                </select>
              </div>
              {[
                { key: "semantic", label: "Semantic Agent (FAISS)" },
                { key: "keyword", label: "Keyword Agent (BM25)" },
                { key: "conceptual", label: "Conceptual Agent (LLM)" },
              ].map(({ key, label }) => (
                <CheckRow
                  key={key}
                  id={`co-rag-${key}`}
                  label={label}
                  checked={coRagConfig[key]}
                  onChange={(v) => dispatch(setCoRagConfig({ [key]: v }))}
                />
              ))}
            </div>
          )}
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
            {!hasDocs
              ? "Tải tài liệu để kích hoạt"
              : coRagEnabled
                ? "Hybrid & Re-ranking bị bypass"
                : "Dùng RAG thông thường"}
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function SectionLabel({ label }) {
  return (
    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-2">
      {label}
    </p>
  );
}

function ToggleRow({ id, label, checked, disabled, onChange }) {
  return (
    <label
      className={cn(
        "flex items-center gap-2 cursor-pointer",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <div className="relative">
        <input
          id={id}
          type="checkbox"
          className="sr-only peer"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
        />
        <div className="w-9 h-5 bg-slate-200 dark:bg-slate-700 peer-checked:bg-blue-600 rounded-full transition-colors peer-disabled:opacity-50" />
        <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
      </div>
      <span className="text-xs font-medium text-slate-700 dark:text-slate-300">{label}</span>
    </label>
  );
}

function CheckRow({ id, label, checked, onChange }) {
  return (
    <label className="flex items-center gap-1.5 cursor-pointer">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-slate-300 dark:border-slate-600 text-blue-600"
      />
      <span className="text-[11px] text-slate-600 dark:text-slate-400">{label}</span>
    </label>
  );
}

export default SearchSettings;
