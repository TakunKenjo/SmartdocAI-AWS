import { useDispatch, useSelector } from "react-redux";
import {
  selectChunkSize,
  selectChunkOverlap,
  setChunkSize,
  setChunkOverlap,
} from "@/store/slices/smartdocSlice.js";

const CHUNK_SIZE_OPTIONS = [500, 1000, 1500, 2000];
const CHUNK_OVERLAP_OPTIONS = [50, 100, 200];

/**
 * ChunkSettings — Selectbox chọn chunk size và overlap
 * Theo design SmartdocAI: 2 select + badge hiển thị cấu hình hiện tại
 */
function ChunkSettings() {
  const dispatch = useDispatch();
  const chunkSize = useSelector(selectChunkSize);
  const chunkOverlap = useSelector(selectChunkOverlap);

  return (
    <div className="space-y-2 mb-3">
      <div>
        <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
          Chunk Size (ký tự)
        </label>
        <select
          value={chunkSize}
          onChange={(e) => dispatch(setChunkSize(Number(e.target.value)))}
          className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-all"
        >
          {CHUNK_SIZE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt} — {opt === 500 ? "Chi tiết" : opt === 1000 ? "Nhỏ" : opt === 1500 ? "Cân bằng" : "Ngữ cảnh rộng"}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
          Chunk Overlap (ký tự)
        </label>
        <select
          value={chunkOverlap}
          onChange={(e) => dispatch(setChunkOverlap(Number(e.target.value)))}
          className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-all"
        >
          {CHUNK_OVERLAP_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt} ký tự
            </option>
          ))}
        </select>
      </div>

      {/* Current config badges */}
      <div className="flex gap-1.5 flex-wrap">
        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full px-2.5 py-0.5">
          Size: {chunkSize}
        </span>
        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-full px-2.5 py-0.5">
          Overlap: {chunkOverlap}
        </span>
      </div>
    </div>
  );
}

export default ChunkSettings;
