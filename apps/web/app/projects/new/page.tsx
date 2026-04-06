import { ProjectWizard } from "@/components/projects/project-wizard";

export default function NewProjectPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Project</h1>
        <p className="text-sm text-muted-foreground">
          Create a new engagement and start compiling your knowledge vault.
        </p>
      </div>
      <ProjectWizard />
    </div>
  );
}
