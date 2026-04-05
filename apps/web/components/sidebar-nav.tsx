"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Database,
  FileText,
  Search,
  Activity,
  LayoutDashboard,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Sources", href: "/dashboard/sources", icon: Database },
  { label: "Vault", href: "/dashboard/vault", icon: FileText },
  { label: "Search", href: "/dashboard/search", icon: Search },
  { label: "Jobs", href: "/dashboard/jobs", icon: Activity },
];

interface SidebarNavProps {
  workspaceSlug?: string;
}

export function SidebarNav({ workspaceSlug }: SidebarNavProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center px-4">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-lg font-bold tracking-tight">Atlas</span>
        </Link>
      </div>
      <Separator />
      {workspaceSlug && (
        <div className="px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Workspace
          </p>
          <p className="mt-1 truncate text-sm font-medium">{workspaceSlug}</p>
        </div>
      )}
      <ScrollArea className="flex-1 px-2 py-2">
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
    </div>
  );
}
