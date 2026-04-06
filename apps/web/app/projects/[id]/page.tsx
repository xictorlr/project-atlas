import Link from "next/link";
import { notFound } from "next/navigation";
import {
  Plus,
  FileText,
  Mic,
  Image as ImageIcon,
  FileSpreadsheet,
  Zap,
  Search,
  BookOpen,
  Wrench,
  Settings,
} from "lucide-react";
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
import { getWorkspace, getSources, getJobs } from "@/lib/api";

export const dynamic = "force-dynamic";

interface ProjectPageProps {
  params: Promise<{ id: string }>;
}

interface SourceFromAPI {
  id: string;
  kind: string;
  status: string;
  title: string | null;
  description: string | null;
  created_at: string;
}

interface JobFromAPI {
  id: string;
  kind: string;
  status: string;
  created_at: string;
}

const PIPELINE_STATUS_STYLES: Record<string, string> = {
  idle: "bg-gray-100 text-gray-700",
  pending: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  ingesting: "bg-blue-100 text-blue-700",
  done: "bg-green-100 text-green-700",
  ready: "bg-green-100 text-green-700",
  succeeded: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

function deriveSourceCounts(sources: SourceFromAPI[]) {
  const counts = { audio: 0, pdf: 0, image: 0, office: 0, other: 0 };
  for (const s of sources) {
    if (s.kind === "audio") counts.audio++;
    else if (s.kind === "pdf") counts.pdf++;
    else if (s.kind === "image") counts.image++;
    else if (["docx", "xlsx", "pptx"].includes(s.kind)) counts.office++;
    else counts.other++;
  }
  return counts;
}

function pipelineStatusFromJobs(jobs: JobFromAPI[]): string {
  if (jobs.length === 0) return "idle";
  const latest = jobs[0];
  return latest.status;
}

export default async function ProjectDashboardPage({ params }: ProjectPageProps) {
  const { id } = await params;

  const [wsResp, sourcesResp, jobsResp] = await Promise.all([
    getWorkspace(id),
    getSources(id),
    getJobs(id),
  ]);

  if (!wsResp.success || !wsResp.data) {
    return notFound();
  }

  const workspace = wsResp.data as unknown as {
    id: string;
    name: string;
    description: string | null;
    slug: string;
  };
  const sources = (sourcesResp.success && Array.isArray(sourcesResp.data)
    ? (sourcesResp.data as unknown as SourceFromAPI[])
    : []);
  const jobs = (jobsResp.success && Array.isArray(jobsResp.data)
    ? (jobsResp.data as unknown as JobFromAPI[])
    : []);

  const sourceCounts = deriveSourceCounts(sources);
  const totalSources = sources.length;
  const pipelineStatus = pipelineStatusFromJobs(jobs);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-2xl font-bold tracking-tight">
              {workspace.name}
            </h1>
            <span
              className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                PIPELINE_STATUS_STYLES[pipelineStatus] ?? PIPELINE_STATUS_STYLES.idle
              }`}
            >
              {pipelineStatus}
            </span>
          </div>
          {workspace.description && (
            <p className="mt-2 text-sm text-muted-foreground">
              {workspace.description}
            </p>
          )}
        </div>

        <Button asChild className="shrink-0">
          <Link href={`/projects/${id}/sources/upload`}>
            <Plus className="mr-1.5 h-4 w-4" />
            Add Sources
          </Link>
        </Button>
      </div>

      {/* Source counts summary */}
      <div className="flex flex-wrap gap-4 rounded-lg border bg-card p-4">
        <SourceCount icon={<Mic className="h-4 w-4 text-purple-600" />} label="Audio" count={sourceCounts.audio} />
        <SourceCount icon={<FileText className="h-4 w-4 text-red-600" />} label="PDF" count={sourceCounts.pdf} />
        <SourceCount icon={<ImageIcon className="h-4 w-4 text-green-600" />} label="Images" count={sourceCounts.image} />
        <SourceCount icon={<FileSpreadsheet className="h-4 w-4 text-blue-600" />} label="Office" count={sourceCounts.office} />
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
          <TabsTrigger value="settings" className="gap-1.5">
            <Settings className="h-3.5 w-3.5" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="mt-4">
          <SourcesTab projectId={id} sources={sources} />
        </TabsContent>

        <TabsContent value="vault" className="mt-4">
          <VaultTab projectId={id} />
        </TabsContent>

        <TabsContent value="search" className="mt-4">
          <SearchTab projectId={id} />
        </TabsContent>

        <TabsContent value="outputs" className="mt-4">
          <OutputsTab projectId={id} />
        </TabsContent>

        <TabsContent value="tools" className="mt-4">
          <ToolsTab projectId={id} />
        </TabsContent>

        <TabsContent value="settings" className="mt-4">
          <SettingsTab projectId={id} />
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

function SourcesTab({ projectId, sources }: { projectId: string; sources: SourceFromAPI[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Sources ({sources.length})</h2>
        <Button asChild size="sm">
          <Link href={`/projects/${projectId}/sources/upload`}>
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add Sources
          </Link>
        </Button>
      </div>
      {sources.length === 0 ? (
        <div className="rounded-lg border border-dashed p-10 text-center">
          <p className="text-sm text-muted-foreground">
            No sources uploaded yet. Click <strong>Add Sources</strong> to get started.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Title</th>
                <th className="px-4 py-2 text-left font-medium">Type</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Added</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id} className="border-t">
                  <td className="px-4 py-2">{s.title || s.id.slice(0, 8)}</td>
                  <td className="px-4 py-2">
                    <Badge variant="outline" className="text-xs">
                      {s.kind}
                    </Badge>
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        PIPELINE_STATUS_STYLES[s.status] ?? PIPELINE_STATUS_STYLES.idle
                      }`}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {new Date(s.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function VaultTab({ projectId }: { projectId: string }) {
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
          Click <strong>Browse vault</strong> to view compiled notes.
        </p>
      </div>
    </div>
  );
}

function SearchTab({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Search</h2>
      <div className="rounded-lg border border-dashed p-10 text-center">
        <p className="text-sm text-muted-foreground">
          Use the global search at <Link href={`/search?ws=${projectId}`} className="underline">/search</Link>.
        </p>
      </div>
    </div>
  );
}

function OutputsTab({ projectId }: { projectId: string }) {
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
          Generate reports, briefs, and digests from the Outputs page.
        </p>
      </div>
    </div>
  );
}

function ToolsTab({ projectId }: { projectId: string }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <QuickActionCard
        href={`/projects/${projectId}/tools`}
        title="DeerFlow Research"
        description="Multi-step research grounded in your vault."
        color="text-blue-600"
      />
      <QuickActionCard
        href={`/projects/${projectId}/tools`}
        title="Hermes Context"
        description="Resume session context from previous work."
        color="text-indigo-600"
      />
      <QuickActionCard
        href={`/projects/${projectId}/tools`}
        title="MiroFish Simulation"
        description="What-if scenarios (requires confirmation)."
        color="text-amber-600"
        premium
      />
    </div>
  );
}

function SettingsTab({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Project Settings</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <QuickActionCard
          href="/settings/models"
          title="Model Management"
          description="Configure which Ollama model is used for compilation."
          color="text-blue-600"
        />
        <QuickActionCard
          href="/settings"
          title="General Settings"
          description="Workspace defaults and global preferences."
          color="text-muted-foreground"
        />
      </div>
      <div className="text-xs text-muted-foreground">
        Project ID: <code>{projectId}</code>
      </div>
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
