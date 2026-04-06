import { notFound } from "next/navigation";
import { ChatPanel } from "@/components/chat/chat-panel";
import { getWorkspace } from "@/lib/api";

export const dynamic = "force-dynamic";

interface ChatPageProps {
  params: Promise<{ id: string }>;
}

export default async function ChatPage({ params }: ChatPageProps) {
  const { id } = await params;
  const wsResp = await getWorkspace(id);

  if (!wsResp.success || !wsResp.data) {
    return notFound();
  }

  const workspace = wsResp.data as unknown as { name: string };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Ask anything about this project. Grounded in your vault via RAG.
        </p>
      </div>
      <ChatPanel projectId={id} projectName={workspace.name} />
    </div>
  );
}
