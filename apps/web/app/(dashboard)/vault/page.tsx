import { NoteList } from "@/components/vault/note-list";
import { getVaultNotes } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function VaultPage() {
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";
  const result = await getVaultNotes(workspaceId).catch(() => null);
  const notes = result?.data ?? [];

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Vault</h1>
        <p className="text-muted-foreground">
          Compiled Markdown notes — sources, entities, concepts, and indexes.
        </p>
      </div>

      <div className="flex-1 overflow-hidden">
        <NoteList notes={notes} />
      </div>
    </div>
  );
}
