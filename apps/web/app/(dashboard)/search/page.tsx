import { Suspense } from "react";
import { SearchBar } from "@/components/search/search-bar";
import { SearchResults } from "@/components/search/search-results";
import { searchVault } from "@/lib/api";

export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Promise<{ q?: string }>;
}

export default async function SearchPage({ searchParams }: PageProps) {
  const { q } = await searchParams;
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";

  const hits =
    q
      ? (await searchVault(workspaceId, q).catch(() => null))?.data ?? []
      : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Search</h1>
        <p className="text-muted-foreground">
          Find notes, entities, and concepts across the vault.
        </p>
      </div>

      <Suspense>
        <SearchBar />
      </Suspense>

      {q && (
        <SearchResults hits={hits} query={q} workspaceId={workspaceId} />
      )}

      {!q && (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <p className="text-sm text-muted-foreground">
            Enter a query above to search the vault.
          </p>
        </div>
      )}
    </div>
  );
}
