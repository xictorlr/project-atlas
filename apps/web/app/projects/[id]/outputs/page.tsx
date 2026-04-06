import { Sparkles } from "lucide-react";
import { OutputCard, type OutputCardData } from "@/components/outputs/output-card";
import { OutputGenerator } from "@/components/outputs/output-generator";
import { OutputArtifactKind } from "@atlas/shared";

export const dynamic = "force-dynamic";

interface OutputsPageProps {
  params: Promise<{ id: string }>;
}

// Placeholder data — replace with getOutputs(projectId) in production
const MOCK_OUTPUTS: OutputCardData[] = [
  {
    id: "out-1",
    title: "LATAM Market Sizing — Status Report Week 12",
    kind: OutputArtifactKind.StatusReport,
    modelUsed: "llama3.2",
    createdAt: new Date(Date.now() - 172_800_000).toISOString(),
    preview:
      "This week's analysis confirms that Brazil and Mexico represent 67% of the addressable market. Key risks include regulatory complexity in Colombia…",
  },
  {
    id: "out-2",
    title: "Acme Corp Executive Brief — Q4 2025",
    kind: OutputArtifactKind.ClientBrief,
    modelUsed: "llama3.1:70b",
    createdAt: new Date(Date.now() - 86_400_000).toISOString(),
    preview:
      "Executive summary of competitive positioning and recommended go-to-market strategy for LATAM expansion phase one.",
  },
  {
    id: "out-3",
    title: "Risk Register v2",
    kind: OutputArtifactKind.RiskRegister,
    createdAt: new Date(Date.now() - 43_200_000).toISOString(),
    preview: "Updated risk register with 14 identified risks, 3 critical, 6 high.",
  },
];

export default async function OutputsPage({ params }: OutputsPageProps) {
  const { id } = await params;
  const outputs = MOCK_OUTPUTS;

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
