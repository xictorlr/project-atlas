import { Sparkles } from "lucide-react";
import { OutputCard, type OutputCardData } from "@/components/outputs/output-card";
import { OutputGenerator } from "@/components/outputs/output-generator";
import { OutputArtifactKind } from "@atlas/shared";
import { getOutputs } from "@/lib/api";

export const dynamic = "force-dynamic";

interface OutputsPageProps {
  params: Promise<{ id: string }>;
}

interface NoteFromAPI {
  slug: string;
  title?: string;
  type?: string;
  output_kind?: string;
  model?: string;
  generated_at?: string;
  created_at?: string;
  preview?: string;
}

function noteToOutputCard(note: NoteFromAPI): OutputCardData {
  const kindMap: Record<string, string> = {
    status_report: OutputArtifactKind.StatusReport,
    client_brief: OutputArtifactKind.ClientBrief,
    weekly_digest: OutputArtifactKind.WeeklyDigest,
    risk_register: OutputArtifactKind.RiskRegister,
    raci_matrix: OutputArtifactKind.RaciMatrix,
    followup_email: OutputArtifactKind.FollowupEmail,
    mermaid_diagram: OutputArtifactKind.MermaidDiagram,
    custom: OutputArtifactKind.Custom,
  };
  const kind = (note.output_kind && kindMap[note.output_kind]) || OutputArtifactKind.Brief;
  return {
    id: note.slug,
    title: note.title || note.slug,
    kind: kind as OutputArtifactKind,
    modelUsed: note.model,
    createdAt: note.generated_at || note.created_at || new Date().toISOString(),
    preview: note.preview || "",
  };
}

export default async function OutputsPage({ params }: OutputsPageProps) {
  const { id } = await params;
  const response = await getOutputs(id);
  const outputs: OutputCardData[] =
    response.success && Array.isArray(response.data)
      ? (response.data as unknown as NoteFromAPI[]).map(noteToOutputCard)
      : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Outputs</h1>
          <p className="text-sm text-muted-foreground">
            Generated reports, briefs, digests, and other artifacts.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* Output grid */}
        <div className="space-y-4">
          <h2 className="font-semibold">
            Generated artifacts
            {outputs.length > 0 && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({outputs.length})
              </span>
            )}
          </h2>

          {outputs.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {outputs.map((output) => (
                <OutputCard key={output.id} output={output} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
              <Sparkles className="mb-3 h-8 w-8 text-muted-foreground" />
              <p className="font-medium">No outputs yet</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Use the generator on the right to create your first artifact.
              </p>
            </div>
          )}
        </div>

        {/* Generator panel (sidebar) */}
        <div className="shrink-0">
          <OutputGenerator projectId={id} />
        </div>
      </div>
    </div>
  );
}
