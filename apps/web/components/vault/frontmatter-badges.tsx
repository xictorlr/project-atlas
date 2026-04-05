import type { VaultNoteFrontmatter } from "@atlas/shared";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface FrontmatterBadgesProps {
  frontmatter: VaultNoteFrontmatter;
}

export function FrontmatterBadges({ frontmatter }: FrontmatterBadgesProps) {
  return (
    <div className="rounded-lg border bg-muted/40 p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="capitalize">
          {frontmatter.kind}
        </Badge>
        {frontmatter.tags.map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">
            {tag}
          </Badge>
        ))}
      </div>

      <Separator className="my-3" />

      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-xs">
        <dt className="text-muted-foreground">Generated</dt>
        <dd>{new Date(frontmatter.generatedAt).toLocaleString()}</dd>

        {frontmatter.model && (
          <>
            <dt className="text-muted-foreground">Model</dt>
            <dd className="font-mono">{frontmatter.model}</dd>
          </>
        )}

        {frontmatter.sourceIds.length > 0 && (
          <>
            <dt className="text-muted-foreground">Sources</dt>
            <dd>{frontmatter.sourceIds.length} linked</dd>
          </>
        )}

        {frontmatter.backlinks.length > 0 && (
          <>
            <dt className="text-muted-foreground">Backlinks</dt>
            <dd>{frontmatter.backlinks.join(", ")}</dd>
          </>
        )}

        {frontmatter.confidenceNotes && (
          <>
            <dt className="text-muted-foreground">Confidence</dt>
            <dd>{frontmatter.confidenceNotes}</dd>
          </>
        )}
      </dl>
    </div>
  );
}
