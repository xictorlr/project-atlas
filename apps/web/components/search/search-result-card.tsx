import Link from "next/link";
import type { SearchHit } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

const KIND_COLORS: Record<string, string> = {
  source: "bg-blue-100 text-blue-800",
  entity: "bg-purple-100 text-purple-800",
  concept: "bg-green-100 text-green-800",
  index: "bg-gray-100 text-gray-800",
  timeline: "bg-orange-100 text-orange-800",
};

interface SearchResultCardProps {
  hit: SearchHit;
  query: string;
  onBuildEvidence?: (hit: SearchHit) => void;
  selected?: boolean;
}

function highlightSnippet(snippet: string, query: string): React.ReactNode {
  if (!query.trim()) return snippet;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = snippet.split(regex);
  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark key={i} className="rounded bg-yellow-100 px-0.5 text-yellow-900">
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

export function SearchResultCard({
  hit,
  query,
  onBuildEvidence,
  selected,
}: SearchResultCardProps) {
  return (
    <div
      className={`rounded-lg border p-4 transition-colors ${
        selected ? "border-primary bg-accent/50" : "hover:bg-accent/30"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/dashboard/vault/${hit.slug}`}
              className="text-sm font-medium hover:underline"
            >
              {hit.title}
            </Link>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                KIND_COLORS[hit.kind] ?? "bg-gray-100 text-gray-800"
              }`}
            >
              {hit.kind}
            </span>
          </div>
          <p className="mt-1.5 text-sm text-muted-foreground line-clamp-3">
            {highlightSnippet(hit.snippet, query)}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <span className="text-xs text-muted-foreground">
            {(hit.score * 100).toFixed(0)}%
          </span>
          {onBuildEvidence && (
            <button
              onClick={() => onBuildEvidence(hit)}
              className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-accent"
            >
              + Evidence
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
