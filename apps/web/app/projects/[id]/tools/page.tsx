import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { DeerFlowPanel } from "@/components/tools/deerflow-panel";
import { HermesPanel } from "@/components/tools/hermes-panel";
import { MiroFishPanel } from "@/components/tools/mirofish-panel";

export const dynamic = "force-dynamic";

interface ToolsPageProps {
  params: Promise<{ id: string }>;
}

export default async function ToolsPage({ params }: ToolsPageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Adapter Tools</h1>
        <p className="text-sm text-muted-foreground">
          Run DeerFlow research, review Hermes context, or launch MiroFish simulations.
        </p>
      </div>

      <Tabs defaultValue="deerflow">
        <TabsList>
          <TabsTrigger value="deerflow">DeerFlow</TabsTrigger>
          <TabsTrigger value="hermes">Hermes</TabsTrigger>
          <TabsTrigger value="mirofish">MiroFish</TabsTrigger>
        </TabsList>

        <TabsContent value="deerflow" className="mt-6">
          <div className="mx-auto max-w-2xl">
            <DeerFlowPanel projectId={id} />
          </div>
        </TabsContent>

        <TabsContent value="hermes" className="mt-6">
          <div className="mx-auto max-w-2xl">
            <HermesPanel projectId={id} />
          </div>
        </TabsContent>

        <TabsContent value="mirofish" className="mt-6">
          <div className="mx-auto max-w-2xl">
            <MiroFishPanel projectId={id} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
