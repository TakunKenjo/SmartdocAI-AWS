import { cn } from "@/lib/utils";
import { User, BrainCircuit } from "lucide-react";
import SourceCitationPanel from "./SourceCitationPanel.jsx";
import SelfRagMetadata from "./SelfRagMetadata.jsx";
import CoRagMetadata from "./CoRagMetadata.jsx";

/**
 * ChatMessage — Bubble cho một tin nhắn (user hoặc assistant)
 * Bao gồm sources, self-rag metadata, co-rag metadata nếu có
 */
function ChatMessage({ message }) {
  const { role, content, sources, searchMode, selfRagMeta, coRagMeta, questionCtx } = message;
  const isUser = role === "user";

  // Badge mode
  const modeBadges = [];
  if (searchMode?.includes("self_rag")) modeBadges.push("Self-RAG");
  else if (searchMode?.includes("co_rag")) modeBadges.push("Co-RAG (Multi-Agent)");
  else if (searchMode?.includes("hybrid")) modeBadges.push("Hybrid Search");
  else if (searchMode) modeBadges.push("Vector Search");
  if (searchMode?.includes("reranked")) modeBadges.push("Cross-Encoder Reranked");

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {/* Avatar for assistant */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm shadow-blue-600/30">
          <BrainCircuit className="h-4 w-4 text-white" />
        </div>
      )}

      <div className={cn("max-w-[80%] space-y-2", isUser && "items-end flex flex-col")}>
        {/* Message bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
            "animate-in slide-in-from-bottom-2 duration-300",
            isUser
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-bl-sm"
          )}
        >
          <p className="whitespace-pre-wrap">{content}</p>
        </div>

        {/* Search mode badge (assistant only) */}
        {!isUser && modeBadges.length > 0 && (
          <p className="text-[10px] text-slate-400 dark:text-slate-500 px-1">
            {modeBadges.join(" · ")}
          </p>
        )}

        {/* Self-RAG metadata */}
        {!isUser && selfRagMeta && <SelfRagMetadata meta={selfRagMeta} />}

        {/* Co-RAG metadata */}
        {!isUser && coRagMeta && <CoRagMetadata meta={coRagMeta} />}

        {/* Sources */}
        {!isUser && sources?.length > 0 && (
          <SourceCitationPanel
            sources={sources}
            question={questionCtx}
            answer={content}
          />
        )}
      </div>

      {/* Avatar for user */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="h-4 w-4 text-slate-500 dark:text-slate-400" />
        </div>
      )}
    </div>
  );
}

export default ChatMessage;
