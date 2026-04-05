import { UploadForm } from "@/components/sources/upload-form";

export default function UploadSourcePage() {
  const workspaceId = process.env.DEFAULT_WORKSPACE_ID ?? "default";
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Upload source</h1>
        <p className="text-muted-foreground">
          Add a document or dataset to the workspace for ingestion and
          compilation.
        </p>
      </div>

      <UploadForm workspaceId={workspaceId} apiBaseUrl={apiBaseUrl} />
    </div>
  );
}
