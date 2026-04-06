import Link from "next/link";
import { Plus, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectCard, type ProjectCardData } from "@/components/projects/project-card";
import { InferenceStatus } from "@/components/inference-status";
import { getProjects } from "@/lib/api";

export const dynamic = "force-dynamic";

interface WorkspaceFromAPI {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

function workspaceToCard(ws: WorkspaceFromAPI): ProjectCardData {
  return {
    id: ws.id,
    name: ws.name,
    slug: ws.slug,
    client: undefined,
    description: ws.description ?? undefined,
    sourceCounts: {},
    pipelineStatus: "idle",
    lastActivityAt: ws.updated_at,
  };
}

export default async function ProjectsPage() {
  const response = await getProjects();
  const projects: ProjectCardData[] =
    response.success && response.data
      ? (response.data as unknown as WorkspaceFromAPI[]).map(workspaceToCard)
      : [];
  const apiError = !response.success ? response.error : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-sm text-muted-foreground">
            {projects.length} active engagement{projects.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <InferenceStatus />
          <Button asChild>
            <Link href="/projects/new">
              <Plus className="mr-1.5 h-4 w-4" />
              New Project
            </Link>
          </Button>
        </div>
      </div>

      {apiError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          API error: {apiError}
        </div>
      )}

      {/* Grid */}
      {projects.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-16 text-center">
          <FolderOpen className="mb-4 h-10 w-10 text-muted-foreground" />
          <h2 className="text-lg font-semibold">No projects yet</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your first project to start compiling knowledge.
          </p>
          <Button asChild className="mt-4">
            <Link href="/projects/new">
              <Plus className="mr-1.5 h-4 w-4" />
              New Project
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}
