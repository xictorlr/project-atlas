"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import type { Source } from "@atlas/shared";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  ingesting: "bg-blue-100 text-blue-800",
  ready: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

interface SourceTableProps {
  sources: Source[];
  onDelete?: (id: string) => void;
}

export function SourceTable({ sources, onDelete }: SourceTableProps) {
  if (sources.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-12 text-center">
        <p className="text-sm text-muted-foreground">
          No sources yet.{" "}
          <Link
            href="/dashboard/sources/upload"
            className="font-medium underline underline-offset-4"
          >
            Upload your first source
          </Link>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-24 text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sources.map((source) => (
            <TableRow key={source.id}>
              <TableCell className="font-medium">
                <Link
                  href={`/dashboard/sources/${source.id}`}
                  className="hover:underline"
                >
                  {source.title}
                </Link>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className="capitalize">
                  {source.kind.replace("_", " ")}
                </Badge>
              </TableCell>
              <TableCell>
                <span
                  className={cn(
                    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
                    STATUS_COLORS[source.status] ?? "bg-gray-100 text-gray-800"
                  )}
                >
                  {source.status}
                </span>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(source.createdAt), {
                  addSuffix: true,
                })}
              </TableCell>
              <TableCell className="text-right">
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => onDelete(source.id)}
                  >
                    Delete
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
