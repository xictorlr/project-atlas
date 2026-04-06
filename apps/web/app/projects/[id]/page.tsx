import Link from "next/link";
import { Plus, FileText, Mic, Image, FileSpreadsheet, Zap, Search, BookOpen, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

export const dynamic = "force-dynamic";

interface ProjectPageProps {
  params: Promise<{ id: string }>;
}

// Placeholder — in production fetch from API using params.id
const MOCK_PROJECT = {
  id: "proj-1",
  name: "Acme Corp Market Analysis",
  client: "Acme Corp",
  description: "Competitive landscape and market sizing for LATAM expansion.",
  sourceCounts: { audio: 3, pdf: 12, image: 2, office: 4 },
  vaultNoteCount: 34,
  pipelineStatus: "done" as const,
  lastActivityAt: new Date(Date.now() - 86_400_000).toISOString(),
};

const PIPELINE_STATUS_STYLES: Record<string, string> = {
  idle: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  done: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default async function ProjectDashboardPage({ params }: ProjectPageProps) {
  const { id } = await params;
  const project = { ...MOCK_PROJECT, id };

  const totalSources =
    project.sourceCounts.audio +
    project.sourceCounts.pdf +
    project.sourceCounts.image +
    project.sourceCounts.office;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-2xl font-bold tracking-tight">
              {project.name}
            </h1>
            <span
              className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                PIPELINE_STATUS_STYLES[project.pipelineStatus]
              }`}
            >
              {project.pipelineStatus}
            </span>
          </div>
          {project.client && (
            <Badge variant="secondary" className="mt-1">
              {project.client}
            </Badge>
          )}
          {project.description && (
            <p className="mt-2 text-sm text-muted-foreground">
              {project.description}
            </p>
          )}
        </div>

        {/* Always-visible Add Sources button */}
        <Button asChild className="shrink-0">
          <Link href={`/projects/${id}/sources/upload`}>
            <Plus className="mr-1.5 h-4 w-4" />
            Add Sources
          </Link>
        </Button>
      </div>

      {/* Source counts summary */}
      <div className="flex flex-wrap gap-4 rounded-lg border bg-card p-4">
        <SourceCount icon={<Mic className="h-4 w-4 text-purple-600" />} label="Audio" count={project.sourceCounts.audio} />
        <SourceCount icon={<FileText className="h-4 w-4 text-red-600" />} label="PDF" count={project.sourceCounts.pdf} />
        <SourceCount icon={<Image className="h-4 w-4 text-green-600" />} label="Images" count={project.sourceCounts.image} />
        <SourceCount icon={<FileSpreadsheet className="h-4 w-4 text-blue-600" />} label="Office" count={project.sourceCounts.office} />
        <div className="ml-auto flex items-center gap-1.5 text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">{totalSources}</span>
          total sources
        </div>
      </div>

      {/* Tabbed content */}
      <Tabs defaultValue="sources">
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="sources" className="gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            Sources
          </TabsTrigger>
          <TabsTrigger value="vault" className="gap-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            Vault
            <Badge variant="secondary" className="ml-1 text-xs">
              {project.vaultNoteCount}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="search" className="gap-1.5">
            <Search className="h-3.5 w-3.5" />
            Search
          </TabsTrigger>
          <TabsTrigger value="outputs" className="gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            Outputs
          </TabsTrigger>
          <TabsTrigger value="tools" className="gap-1.5">
            <Wrench className="h-3.5 w-3.5" />
            Tools
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="mt-4">
          <SourcesTabContent projectId={id} />
        </TabsContent>

        <TabsContent value="vault" className="mt-4">
          <VaultTabContent projectId={id} />
        </TabsContent>

        <TabsContent value="search" className="mt-4">
          <SearchTabContent projectId={id} />
        </TabsContent>

        <TabsContent value="outputs" className="mt-4">
          <OutputsTabContent projectId={id} />
        </TabsContent>

        <TabsContent value="tools" className="mt-4">
          <ToolsTabContent projectId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function SourceCount({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center gap-1.5 text-sm">
      {icon}
      <span className="font-medium">{count}</span>
      <span className="text-muted-foreground">{label}</span>
    </div>
  );
}

function SourcesTabContent({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Sources</h2>
        <Button asChild size="sm">
          <Link href={`/projects/${projectId}/sources/upload`}>
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add Sources
          </Link>
        </Button>
      </div>
      <div className="rounded-lg border border-dashed p-10 text-center">
        <p className="text-sm text-muted-foreground">
          Source list loads here — connect to{" "}
          <code className="text-xs">getSources(projectId)</code> to populate.
        </p>
      </div>
    </div>
  );
}

function VaultTabContent({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Vault Notes</h2>
        <Button asChild size="sm" variant="outline">
          <Link href={`/projects/${projectId}/vault`}>Browse vault</Link>
        </Button>
      </div>
      <div className="rounded-lg border border-dashed p-10 text-center">
        <p className="text-sm text-muted-foreground">
          Vault note list loads here — connect to{" "}
          <code className="text-xs">getVaultNotes(projectId)</code> to populate.
        </p>
      </div>
    </div>
  );
}

function SearchTabContent({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Search</h2>
      <div className="rounded-lg border border-dashed p-10 text-center">
        <p className="text-sm text-muted-foreground">
          Full search UI loads here — uses{" "}
          <code className="text-xs">searchVault(projectId, query)</code>.
        </p>
      </div>
    </div>
  );
}

function OutputsTabContent({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Generated Outputs</h2>
        <Button asChild size="sm">
          <Link href={`/projects/${projectId}/outputs`}>
            <Zap className="mr-1 h-3.5 w-3.5" />
            All Outputs
          </Link>
        </Button>
      </div>
      <div className="rounded-lg border border-dashed p-10 text-center">
        <p className="text-sm text-muted-foreground">
          Recent outputs load here — connect to{" "}
          <code className="text-xs">getOutputs(projectId)</code> to populate.
        </p>
      </div>
    </div>
  );
}

function ToolsTabContent({ projectId }: { projectId: string }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <QuickActionCard
        href={`/projects/${projectId}/tools`}
        title="DeerFlow Research"
        description="Run autonomous web research and compile into vault."
        color="text-blue-600"
      />
      <QuickActionCard
        href={`/projects/${projectId}/tools`}
        title="Hermes Context"
        description="Resume or review persistent conversation context."
        color="text-indigo-600"
      />
      <QuickActionCard
        href={`/projects/${projectId}/tools`}
        title="MiroFish Simulation"
        description="Run what-if scenario simulations (requires confirmation)."
        color="text-amber-600"
        premium
      />
    </div>
  );
}

function QuickActionCard({
  href,
  title,
  description,
  color,
  premium,
}: {
  href: string;
  title: string;
  description: string;
  color: string;
  premium?: boolean;
}) {
  return (
    <Link href={href}>
      <Card className="h-full cursor-pointer transition-shadow hover:shadow-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className={`text-sm ${color}`}>{title}</CardTitle>
            {premium && (
              <Badge variant="outline" className="text-xs">
                Premium
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <CardDescription className="text-xs">{description}</CardDescription>
        </CardContent>
      </Card>
    </Link>
  );
}
