"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FolderOpen,
  Plus,
  LayoutDashboard,
  Settings,
  Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const TOP_NAV: NavItem[] = [
  { label: "Projects", href: "/projects", icon: FolderOpen },
  { label: "New Project", href: "/projects/new", icon: Plus },
];

const BOTTOM_NAV: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Models", href: "/settings/models", icon: Cpu },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function ProjectsSidebarNav() {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === "/projects") {
      return pathname === "/projects";
    }
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center px-4">
        <Link href="/projects" className="flex items-center gap-2">
          <span className="text-lg font-bold tracking-tight">Atlas</span>
        </Link>
      </div>
      <Separator />

      <ScrollArea className="flex-1 px-2 py-2">
        <nav className="space-y-1">
          {TOP_NAV.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
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

      <Separator />
      <div className="px-2 py-2">
        <nav className="space-y-1">
          {BOTTOM_NAV.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
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
      </div>
    </div>
  );
}
