import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SourceDetail } from "@/components/sources/source-detail";
import { apiFetch } from "@/lib/api-internal";
import type { Source } from "@atlas/shared";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function SourceDetailPage({ params }: PageProps) {
  const { id } = await params;
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";

  const result = await apiFetch<Source>(
    `/api/v1/workspaces/${workspaceId}/sources/${id}`
  ).catch(() => null);

  if (!result?.data) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/dashboard/sources">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to sources
        </Link>
      </Button>

      <SourceDetail source={result.data} />
    </div>
  );
}
