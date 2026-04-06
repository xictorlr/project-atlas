"use client";

import { useRef, useState, useCallback } from "react";
import {
  Mic,
  FileText,
  Image,
  FileSpreadsheet,
  Presentation,
  File,
  X,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface UploadFile {
  id: string;
  file: File;
  type: FileCategory;
}

type FileCategory =
  | "audio"
  | "pdf"
  | "image"
  | "word"
  | "excel"
  | "powerpoint"
  | "markdown"
  | "text"
  | "html"
  | "other";

const ACCEPTED = [
  ".mp3,.wav,.m4a,.ogg,.webm",
  ".pdf",
  ".jpg,.jpeg,.png,.webp,.tiff",
  ".docx",
  ".xlsx,.csv",
  ".pptx",
  ".md",
  ".txt",
  ".html,.htm",
].join(",");

function categorize(file: File): FileCategory {
  const name = file.name.toLowerCase();
  const mime = file.type.toLowerCase();
  if (mime.startsWith("audio/") || /\.(mp3|wav|m4a|ogg|webm)$/.test(name)) return "audio";
  if (mime === "application/pdf" || name.endsWith(".pdf")) return "pdf";
  if (mime.startsWith("image/") || /\.(jpg|jpeg|png|webp|tiff)$/.test(name)) return "image";
  if (name.endsWith(".docx")) return "word";
  if (name.endsWith(".xlsx") || name.endsWith(".csv")) return "excel";
  if (name.endsWith(".pptx")) return "powerpoint";
  if (name.endsWith(".md")) return "markdown";
  if (mime === "text/plain" || name.endsWith(".txt")) return "text";
  if (mime === "text/html" || name.endsWith(".html") || name.endsWith(".htm")) return "html";
  return "other";
}

const CATEGORY_ICONS: Record<FileCategory, React.ElementType> = {
  audio: Mic,
  pdf: FileText,
  image: Image,
  word: FileText,
  excel: FileSpreadsheet,
  powerpoint: Presentation,
  markdown: FileText,
  text: FileText,
  html: FileText,
  other: File,
};

const CATEGORY_COLORS: Record<FileCategory, string> = {
  audio: "text-purple-600",
  pdf: "text-red-600",
  image: "text-green-600",
  word: "text-blue-600",
  excel: "text-emerald-600",
  powerpoint: "text-orange-600",
  markdown: "text-indigo-600",
  text: "text-gray-600",
  html: "text-yellow-600",
  other: "text-gray-500",
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface MultiUploaderProps {
  files: UploadFile[];
  onFilesChange: (files: UploadFile[]) => void;
}

export function MultiUploader({ files, onFilesChange }: MultiUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function addFiles(incoming: FileList | File[]) {
    const arr = Array.from(incoming);
    const newEntries: UploadFile[] = arr.map((f) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file: f,
      type: categorize(f),
    }));
    onFilesChange([...files, ...newEntries]);
  }

  function removeFile(id: string) {
    onFilesChange(files.filter((f) => f.id !== id));
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files);
      }
    },
    [files] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop files here or click to browse"
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          dragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/30"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      >
        <UploadCloud className="h-8 w-8 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">Drop files here or click to browse</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Audio, PDF, Word, Excel, PowerPoint, Images, Markdown, Text
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => {
            if (e.target.files) {
              addFiles(e.target.files);
              e.target.value = "";
            }
          }}
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map(({ id, file, type }) => {
            const Icon = CATEGORY_ICONS[type];
            const colorClass = CATEGORY_COLORS[type];
            return (
              <li
                key={id}
                className="flex items-center gap-3 rounded-md border bg-card px-3 py-2"
              >
                <Icon className={cn("h-4 w-4 shrink-0", colorClass)} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {type} · {formatBytes(file.size)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 text-muted-foreground hover:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(id);
                  }}
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="h-3 w-3" />
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      {files.length > 0 && (
        <p className="text-right text-xs text-muted-foreground">
          {files.length} file{files.length !== 1 ? "s" : ""} selected
        </p>
      )}
    </div>
  );
}
