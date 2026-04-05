import { Button } from "@/components/ui/button";
import { JobTable } from "@/components/jobs/job-table";
import { getJobs } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function JobsPage() {
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";
  const result = await getJobs(workspaceId).catch(() => null);
  const jobs = result?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Jobs</h1>
          <p className="text-muted-foreground">
            Pipeline runs — ingest, compile, index, and publish.
          </p>
        </div>
        <RecompileButton workspaceId={workspaceId} />
      </div>

      <JobTable initialJobs={jobs} workspaceId={workspaceId} />
    </div>
  );
}

function RecompileButton({ workspaceId }: { workspaceId: string }) {
  return (
    <form
      action={async () => {
        "use server";
        const { apiFetch } = await import("@/lib/api");
        await apiFetch(`/api/v1/workspaces/${workspaceId}/jobs`, {
          method: "POST",
          body: JSON.stringify({ kind: "compile" }),
        });
      }}
    >
      <Button type="submit" variant="outline">
        Recompile vault
      </Button>
    </form>
  );
}
