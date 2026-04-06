"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { FileText, Mic, Image, FileSpreadsheet, ArrowRight } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface ProjectCardData {
  id: string;
  name: string;
  slug: string;
  client?: string;
  description?: string;
  sourceCounts?: {
    audio?: number;
    pdf?: number;
    image?: number;
    office?: number;
    other?: number;
  };
  pipelineStatus?: "idle" | "running" | "done" | "failed";
  lastActivityAt?: string;
}

interface ProjectCardProps {
  project: ProjectCardData;
}

const PIPELINE_STATUS_STYLES: Record<string, string> = {
  idle: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  done: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export function ProjectCard({ project }: ProjectCardProps) {
  const {
    id,
    name,
    client,
    description,
    sourceCounts = {},
    pipelineStatus = "idle",
    lastActivityAt,
  } = project;

  const totalSources =
    (sourceCounts.audio ?? 0) +
    (sourceCounts.pdf ?? 0) +
    (sourceCounts.image ?? 0) +
    (sourceCounts.office ?? 0) +
    (sourceCounts.other ?? 0);

  return (
    <Card className="flex flex-col transition-shadow hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <CardTitle className="truncate text-base">{name}</CardTitle>
            {client && (
              <Badge variant="secondary" className="mt-1 text-xs">
                {client}
              </Badge>
            )}
          </div>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
              PIPELINE_STATUS_STYLES[pipelineStatus]
            }`}
          >
            {pipelineStatus}
          </span>
        </div>
        {description && (
          <CardDescription className="mt-1 line-clamp-2 text-xs">
            {description}
          </CardDescription>
        )}
      </CardHeader>

      <CardContent className="flex-1 pb-3">
        <div className="flex flex-wrap gap-2">
          {(sourceCounts.audio ?? 0) > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Mic className="h-3 w-3" />
              {sourceCounts.audio} audio
            </span>
          )}
          {(sourceCounts.pdf ?? 0) > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <FileText className="h-3 w-3" />
              {sourceCounts.pdf} PDF
            </span>
          )}
          {(sourceCounts.image ?? 0) > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Image className="h-3 w-3" />
              {sourceCounts.image} image
            </span>
          )}
          {(sourceCounts.office ?? 0) > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <FileSpreadsheet className="h-3 w-3" />
              {sourceCounts.office} office
            </span>
          )}
          {totalSources === 0 && (
            <span className="text-xs text-muted-foreground">No sources yet</span>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between border-t pt-3">
        {lastActivityAt ? (
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(lastActivityAt), { addSuffix: true })}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">No activity</span>
        )}
        <Button asChild size="sm" variant="ghost" className="gap-1 text-xs">
          <Link href={`/projects/${id}`}>
            Open <ArrowRight className="h-3 w-3" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
