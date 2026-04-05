import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SourceTable } from "@/components/sources/source-table";
import { getSources } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SourcesPage() {
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";
  const result = await getSources(workspaceId).catch(() => null);
  const sources = result?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sources</h1>
          <p className="text-muted-foreground">
            All documents and datasets ingested into this workspace.
          </p>
        </div>
        <Button asChild>
          <Link href="/dashboard/sources/upload">Upload source</Link>
        </Button>
      </div>

      <SourceTable sources={sources} />
    </div>
  );
}
