import type { Job } from "@atlas/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { JobStatusBadge } from "./job-status-badge";

interface JobDetailProps {
  job: Job;
}

function formatDuration(job: Job): string {
  if (!job.startedAt) return "Not started";
  const end = job.completedAt ? new Date(job.completedAt) : new Date();
  const ms = end.getTime() - new Date(job.startedAt).getTime();
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 60000)}m`;
}

export function JobDetail({ job }: JobDetailProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold capitalize tracking-tight">
          {job.kind.replace("_", " ")} job
        </h1>
        <JobStatusBadge status={job.status} />
      </div>

      {/* Timing */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Timing</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Queued</span>
            <span>{new Date(job.queuedAt).toLocaleString()}</span>
          </div>
          <Separator />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Started</span>
            <span>
              {job.startedAt
                ? new Date(job.startedAt).toLocaleString()
                : "—"}
            </span>
          </div>
          <Separator />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Completed</span>
            <span>
              {job.completedAt
                ? new Date(job.completedAt).toLocaleString()
                : "—"}
            </span>
          </div>
          <Separator />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Duration</span>
            <span>{formatDuration(job)}</span>
          </div>
          <Separator />
          <div className="flex justify-between">
            <span className="text-muted-foreground">Attempt</span>
            <span>
              {job.attempt} / {job.maxAttempts}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {job.error && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-destructive">
              Error
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Code</span>
              <span className="font-mono text-xs">{job.error.code}</span>
            </div>
            <Separator />
            <p className="text-destructive">{job.error.message}</p>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Retryable</span>
              <span>{job.error.retryable ? "Yes" : "No"}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payload */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Input payload</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
            {JSON.stringify(job.payload, null, 2)}
          </pre>
        </CardContent>
      </Card>

      {/* Result */}
      {job.result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Output result</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
              {JSON.stringify(job.result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
