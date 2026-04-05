import Link from "next/link";
import type { Source } from "@atlas/shared";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  ingesting: "bg-blue-100 text-blue-800",
  ready: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

interface SourceDetailProps {
  source: Source;
  vaultNoteSlug?: string;
}

export function SourceDetail({ source, vaultNoteSlug }: SourceDetailProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{source.title}</h1>
          {source.description && (
            <p className="mt-1 text-muted-foreground">{source.description}</p>
          )}
        </div>
        <span
          className={cn(
            "inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
            STATUS_COLORS[source.status] ?? "bg-gray-100 text-gray-800"
          )}
        >
          {source.status}
        </span>
      </div>

      {/* Metadata card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Metadata</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Type</span>
            <Badge variant="outline" className="capitalize">
              {source.kind.replace("_", " ")}
            </Badge>
          </div>
          <Separator />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Storage key</span>
            <span className="truncate pl-4 font-mono text-xs">
              {source.storageKey}
            </span>
          </div>
          <Separator />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{new Date(source.createdAt).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Updated</span>
            <span>{new Date(source.updatedAt).toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>

      {/* Manifest card */}
      {source.manifest && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Ingest Manifest
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {source.manifest.originUrl && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Origin URL</span>
                  <a
                    href={source.manifest.originUrl}
                    className="truncate pl-4 text-primary underline underline-offset-2"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {source.manifest.originUrl}
                  </a>
                </div>
                <Separator />
              </>
            )}
            {source.manifest.mimeType && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">MIME type</span>
                  <span className="font-mono text-xs">
                    {source.manifest.mimeType}
                  </span>
                </div>
                <Separator />
              </>
            )}
            {source.manifest.fileSizeBytes != null && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">File size</span>
                  <span>
                    {(source.manifest.fileSizeBytes / 1024).toFixed(1)} KB
                  </span>
                </div>
                <Separator />
              </>
            )}
            {source.manifest.chunkCount != null && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Chunks</span>
                  <span>{source.manifest.chunkCount}</span>
                </div>
                <Separator />
              </>
            )}
            {source.manifest.model && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model</span>
                  <span className="font-mono text-xs">
                    {source.manifest.model}
                  </span>
                </div>
                <Separator />
              </>
            )}
            {source.manifest.confidenceNotes && (
              <div>
                <p className="text-muted-foreground">Confidence notes</p>
                <p className="mt-1">{source.manifest.confidenceNotes}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Vault link */}
      {vaultNoteSlug && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm">
              Vault note:{" "}
              <Link
                href={`/dashboard/vault/${vaultNoteSlug}`}
                className="font-medium text-primary underline underline-offset-2"
              >
                {vaultNoteSlug}
              </Link>
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
