"use client";

import { useState } from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import type { VaultNote } from "@atlas/shared";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

const KIND_COLORS: Record<string, string> = {
  source: "bg-blue-100 text-blue-800",
  entity: "bg-purple-100 text-purple-800",
  concept: "bg-green-100 text-green-800",
  index: "bg-gray-100 text-gray-800",
  timeline: "bg-orange-100 text-orange-800",
};

interface NoteListProps {
  notes: VaultNote[];
}

export function NoteList({ notes }: NoteListProps) {
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState<string>("all");

  const kinds = ["all", ...Array.from(new Set(notes.map((n) => n.kind)))];

  const filtered = notes.filter((note) => {
    const matchesQuery =
      !query ||
      note.frontmatter.title.toLowerCase().includes(query.toLowerCase()) ||
      note.frontmatter.tags.some((t) =>
        t.toLowerCase().includes(query.toLowerCase())
      );
    const matchesKind = kindFilter === "all" || note.kind === kindFilter;
    return matchesQuery && matchesKind;
  });

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Filters */}
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input
          placeholder="Filter notes..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1"
        />
        <div className="flex flex-wrap gap-1">
          {kinds.map((k) => (
            <button
              key={k}
              onClick={() => setKindFilter(k)}
              className={
                kindFilter === k
                  ? "rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground"
                  : "rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent"
              }
            >
              {k === "all" ? "All" : k}
            </button>
          ))}
        </div>
      </div>

      {/* Note list */}
      {filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <p className="text-sm text-muted-foreground">
            {notes.length === 0 ? "No vault notes yet." : "No notes match the filter."}
          </p>
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <div className="space-y-px">
            {filtered.map((note) => (
              <Link
                key={note.id}
                href={`/dashboard/vault/${note.slug}`}
                className="flex items-start justify-between rounded-md px-3 py-2.5 hover:bg-accent"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {note.frontmatter.title}
                  </p>
                  {note.frontmatter.tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {note.frontmatter.tags.slice(0, 4).map((tag) => (
                        <span
                          key={tag}
                          className="rounded bg-secondary px-1.5 py-0.5 text-[10px] text-muted-foreground"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="ml-4 flex shrink-0 flex-col items-end gap-1">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                      KIND_COLORS[note.kind] ?? "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {note.kind}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {formatDistanceToNow(new Date(note.updatedAt), {
                      addSuffix: true,
                    })}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </ScrollArea>
      )}

      <p className="text-xs text-muted-foreground">
        {filtered.length} of {notes.length} notes
      </p>
    </div>
  );
}
