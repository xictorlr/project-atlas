import Link from "next/link";
import { Plus, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectCard, type ProjectCardData } from "@/components/projects/project-card";
import { InferenceStatus } from "@/components/inference-status";

export const dynamic = "force-dynamic";

// Placeholder project data — replace with getProjects() API call once backend is ready
const MOCK_PROJECTS: ProjectCardData[] = [
  {
    id: "proj-1",
    name: "Acme Corp Market Analysis",
    slug: "acme-market-analysis",
    client: "Acme Corp",
    description: "Competitive landscape and market sizing for LATAM expansion.",
    sourceCounts: { audio: 3, pdf: 12, office: 4 },
    pipelineStatus: "done",
    lastActivityAt: new Date(Date.now() - 86_400_000).toISOString(),
  },
  {
    id: "proj-2",
    name: "Meridian Digital Transformation",
    slug: "meridian-digital",
    client: "Meridian Group",
    description: "ERP migration roadmap and change management strategy.",
    sourceCounts: { pdf: 7, office: 6, image: 2 },
    pipelineStatus: "running",
    lastActivityAt: new Date(Date.now() - 3_600_000).toISOString(),
  },
  {
    id: "proj-3",
    name: "Q1 Strategy Review",
    slug: "q1-strategy",
    description: "Internal strategy review and OKR alignment.",
    sourceCounts: {},
    pipelineStatus: "idle",
    lastActivityAt: undefined,
  },
];

export default function ProjectsPage() {
  const projects = MOCK_PROJECTS;

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
