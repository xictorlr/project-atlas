import { Database, FileText, BookOpen, Activity } from "lucide-react";
import { StatCard } from "@/components/stat-card";
import { getWorkspaceStats } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  // Default workspace — in production this would come from session/params
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";
  const result = await getWorkspaceStats(workspaceId).catch(() => null);
  const stats = result?.data ?? {
    sourceCount: 0,
    noteCount: 0,
    entityCount: 0,
    jobCount: 0,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Overview</h1>
        <p className="text-muted-foreground">
          Workspace at a glance — sources, vault notes, entities, and jobs.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Sources"
          value={stats.sourceCount}
          description="Ingested documents and datasets"
          icon={<Database className="h-4 w-4" />}
        />
        <StatCard
          title="Vault Notes"
          value={stats.noteCount}
          description="Compiled Markdown pages"
          icon={<FileText className="h-4 w-4" />}
        />
        <StatCard
          title="Entities"
          value={stats.entityCount}
          description="Named entities extracted"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          title="Jobs"
          value={stats.jobCount}
          description="Pipeline runs recorded"
          icon={<Activity className="h-4 w-4" />}
        />
      </div>
    </div>
  );
}
