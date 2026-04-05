"use client";

import { useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function SearchBar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const currentQuery = searchParams.get("q") ?? "";

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const q = (fd.get("q") as string).trim();
    if (!q) return;
    startTransition(() => {
      router.push(`/dashboard/search?q=${encodeURIComponent(q)}`);
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          name="q"
          defaultValue={currentQuery}
          placeholder="Search vault notes..."
          className="pl-9"
          autoFocus
        />
      </div>
      <Button type="submit" disabled={isPending}>
        {isPending ? "Searching…" : "Search"}
      </Button>
    </form>
  );
}
