"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { VaultNote } from "@atlas/shared";
import { FrontmatterBadges } from "./frontmatter-badges";
import { renderWithWikilinks } from "./wikilink-renderer";

interface NoteReaderProps {
  note: VaultNote;
  content: string;
}

export function NoteReader({ note, content }: NoteReaderProps) {
  return (
    <article className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {note.frontmatter.title}
        </h1>
        <p className="mt-1 font-mono text-xs text-muted-foreground">
          {note.vaultPath}
        </p>
      </div>

      <FrontmatterBadges frontmatter={note.frontmatter} />

      <div className="prose prose-slate max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p({ children }) {
              const text = typeof children === "string" ? children : null;
              if (text && text.includes("[[")) {
                return <p>{renderWithWikilinks(text)}</p>;
              }
              return <p>{children}</p>;
            },
            a({ href, children }) {
              return (
                <a
                  href={href}
                  target={href?.startsWith("http") ? "_blank" : undefined}
                  rel={
                    href?.startsWith("http") ? "noopener noreferrer" : undefined
                  }
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </article>
  );
}
