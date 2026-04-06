"use client";

import { formatDistanceToNow } from "date-fns";
import {
  FileText,
  BarChart2,
  Mail,
  List,
  GitBranch,
  Calendar,
  AlertTriangle,
  Users,
  Sparkles,
} from "lucide-react";
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
import { OutputArtifactKind } from "@atlas/shared";

export interface OutputCardData {
  id: string;
  title: string;
  kind: string;
  modelUsed?: string;
  createdAt: string;
  preview?: string;
}

interface OutputCardProps {
  output: OutputCardData;
  onView?: (id: string) => void;
}

const KIND_ICONS: Record<string, React.ElementType> = {
  [OutputArtifactKind.StatusReport]: BarChart2,
  [OutputArtifactKind.ClientBrief]: FileText,
  [OutputArtifactKind.WeeklyDigest]: Calendar,
  [OutputArtifactKind.RiskRegister]: AlertTriangle,
  [OutputArtifactKind.RaciMatrix]: Users,
  [OutputArtifactKind.FollowupEmail]: Mail,
  [OutputArtifactKind.MermaidDiagram]: GitBranch,
  [OutputArtifactKind.Custom]: Sparkles,
  [OutputArtifactKind.Brief]: FileText,
  [OutputArtifactKind.SlideDeck]: List,
};

const KIND_LABELS: Record<string, string> = {
  [OutputArtifactKind.StatusReport]: "Status Report",
  [OutputArtifactKind.ClientBrief]: "Client Brief",
  [OutputArtifactKind.WeeklyDigest]: "Weekly Digest",
  [OutputArtifactKind.RiskRegister]: "Risk Register",
  [OutputArtifactKind.RaciMatrix]: "RACI Matrix",
  [OutputArtifactKind.FollowupEmail]: "Follow-up Email",
  [OutputArtifactKind.MermaidDiagram]: "Mermaid Diagram",
  [OutputArtifactKind.Custom]: "Custom",
  [OutputArtifactKind.Brief]: "Brief",
  [OutputArtifactKind.SlideDeck]: "Slide Deck",
};

export function OutputCard({ output, onView }: OutputCardProps) {
  const Icon = KIND_ICONS[output.kind] ?? FileText;
  const kindLabel = KIND_LABELS[output.kind] ?? output.kind;

  return (
    <Card className="flex flex-col transition-shadow hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 shrink-0 rounded-md bg-muted p-2">
            <Icon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <CardTitle className="line-clamp-2 text-sm">{output.title}</CardTitle>
            <div className="mt-1 flex flex-wrap gap-1.5">
              <Badge variant="outline" className="text-xs">
                {kindLabel}
              </Badge>
              {output.modelUsed && (
                <Badge variant="secondary" className="text-xs">
                  {output.modelUsed}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardHeader>

      {output.preview && (
        <CardContent className="flex-1 pb-3">
          <CardDescription className="line-clamp-3 text-xs">
            {output.preview}
          </CardDescription>
        </CardContent>
      )}

      <CardFooter className="flex items-center justify-between border-t pt-3">
        <span className="text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(output.createdAt), { addSuffix: true })}
        </span>
        {onView && (
          <Button
            size="sm"
            variant="ghost"
            className="text-xs"
            onClick={() => onView(output.id)}
          >
            View
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
