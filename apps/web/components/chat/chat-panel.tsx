"use client";

import { useState, useRef, useEffect } from "react";
import { Send, FileText, Bot, User, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { chatWithProject, type ChatSource } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  timestamp: Date;
}

interface ChatPanelProps {
  projectId: string;
  projectName?: string;
}

export function ChatPanel({ projectId, projectName }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  async function handleSend() {
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: `${Date.now()}-u`,
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // Build history from previous messages (last 6 for context)
      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await chatWithProject(projectId, question, history);

      if (!response.success || !response.data) {
        throw new Error(response.error || "Chat request failed");
      }

      const data = response.data;
      const assistantMsg: Message = {
        id: `${Date.now()}-a`,
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get answer");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-260px)] flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">
            Chat with {projectName ?? "this project"}
          </h2>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Ask anything about the project. Answers are grounded in vault notes via RAG.
        </p>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Bot className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm font-medium">Ready to answer</p>
            <p className="mt-1 max-w-sm text-xs text-muted-foreground">
              Try: &quot;What are the key decisions made in this project?&quot;
              or &quot;Summarize the action items from last week&quot;
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div
                className={`flex-1 ${
                  msg.role === "user" ? "max-w-[80%]" : "max-w-[85%]"
                }`}
              >
                <div
                  className={`rounded-lg px-4 py-2 text-sm ${
                    msg.role === "user"
                      ? "ml-auto bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs font-medium text-muted-foreground">
                      Sources:
                    </p>
                    {msg.sources.map((src, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 rounded-md border bg-background p-2 text-xs"
                      >
                        <FileText className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium truncate">
                              {src.note_title}
                            </span>
                            <Badge variant="outline" className="text-[10px]">
                              {(src.relevance * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          <p className="mt-0.5 text-muted-foreground line-clamp-2">
                            {src.passage}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-lg bg-muted px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="border-t bg-destructive/5 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !loading) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask anything about this project..."
            disabled={loading}
            className="flex-1 rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="mt-1.5 text-[11px] text-muted-foreground">
          Press Enter to send. Answers come from your vault via local Ollama (no cloud).
        </p>
      </div>
    </div>
  );
}
