import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { NoteReader } from "@/components/vault/note-reader";
import { getVaultNote, getVaultNoteContent } from "@/lib/api";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function VaultNotePage({ params }: PageProps) {
  const { slug } = await params;
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";

  const [noteResult, contentResult] = await Promise.all([
    getVaultNote(workspaceId, slug).catch(() => null),
    getVaultNoteContent(workspaceId, slug).catch(() => null),
  ]);

  if (!noteResult?.data) {
    notFound();
  }

  const content = contentResult?.data?.content ?? "";

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/dashboard/vault">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to vault
        </Link>
      </Button>

      <NoteReader note={noteResult.data} content={content} />
    </div>
  );
}
