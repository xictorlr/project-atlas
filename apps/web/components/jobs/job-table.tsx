"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import type { Job } from "@atlas/shared";
import { JobStatus } from "@atlas/shared";
import { JobStatusBadge } from "./job-status-badge";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getJobs } from "@/lib/api";

function formatDuration(job: Job): string {
  if (!job.startedAt) return "—";
  const end = job.completedAt ? new Date(job.completedAt) : new Date();
  const ms = end.getTime() - new Date(job.startedAt).getTime();
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 60000)}m`;
}

interface JobTableProps {
  initialJobs: Job[];
  workspaceId: string;
}

const IN_PROGRESS_STATUSES: string[] = [
  JobStatus.Queued,
  JobStatus.Running,
];

export function JobTable({ initialJobs, workspaceId }: JobTableProps) {
  const [jobs, setJobs] = useState<Job[]>(initialJobs);

  const hasActive = jobs.some((j) => IN_PROGRESS_STATUSES.includes(j.status));

  const refresh = useCallback(async () => {
    const result = await getJobs(workspaceId).catch(() => null);
    if (result?.data) setJobs(result.data);
  }, [workspaceId]);

  useEffect(() => {
    if (!hasActive) return;
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [hasActive, refresh]);

  if (jobs.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-12 text-center">
        <p className="text-sm text-muted-foreground">No jobs recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Kind</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Queued</TableHead>
            <TableHead>Error</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {jobs.map((job) => (
            <TableRow key={job.id}>
              <TableCell>
                <Link
                  href={`/dashboard/jobs/${job.id}`}
                  className="font-medium hover:underline"
                >
                  <Badge variant="outline" className="capitalize">
                    {job.kind.replace("_", " ")}
                  </Badge>
                </Link>
              </TableCell>
              <TableCell>
                <JobStatusBadge status={job.status} />
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatDuration(job)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(job.queuedAt), {
                  addSuffix: true,
                })}
              </TableCell>
              <TableCell className="max-w-xs truncate text-sm text-destructive">
                {job.error?.message ?? ""}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {hasActive && (
        <p className="px-4 py-2 text-xs text-muted-foreground">
          Auto-refreshing every 5s while jobs are active.
        </p>
      )}
    </div>
  );
}
