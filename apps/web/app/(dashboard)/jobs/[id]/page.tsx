import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { JobDetail } from "@/components/jobs/job-detail";
import { getJob } from "@/lib/api";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function JobDetailPage({ params }: PageProps) {
  const { id } = await params;
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";

  const result = await getJob(workspaceId, id).catch(() => null);

  if (!result?.data) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/dashboard/jobs">
          <ChevronLeft className="mr-1 h-4 w-4" />
          Back to jobs
        </Link>
      </Button>

      <JobDetail job={result.data} />
    </div>
  );
}
