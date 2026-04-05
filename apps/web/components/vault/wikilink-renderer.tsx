"use client";

import Link from "next/link";

/**
 * Renders a [[wikilink]] pattern as an internal /dashboard/vault/:slug link.
 * Used as a custom component in react-markdown.
 */
export function renderWithWikilinks(text: string): React.ReactNode[] {
  const parts = text.split(/(\[\[([^\]]+)\]\])/g);
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < parts.length) {
    const part = parts[i];
    if (part?.startsWith("[[") && part.endsWith("]]")) {
      const inner = parts[i + 1] ?? part.slice(2, -2);
      const [display, slug] = inner.includes("|")
        ? inner.split("|", 2)
        : [inner, inner.toLowerCase().replace(/\s+/g, "-")];
      result.push(
        <Link
          key={i}
          href={`/dashboard/vault/${slug}`}
          className="font-medium text-primary underline underline-offset-2"
        >
          {display}
        </Link>
      );
      i += 2;
    } else if (part) {
      result.push(<span key={i}>{part}</span>);
      i += 1;
    } else {
      i += 1;
    }
  }

  return result;
}
