"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

interface SettingsNavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const SETTINGS_NAV: SettingsNavItem[] = [
  { label: "Models", href: "/settings/models", icon: Cpu },
  { label: "General", href: "/settings", icon: Settings2 },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="grid min-h-screen md:grid-cols-[220px_1fr]">
      {/* Settings sidebar */}
      <aside className="hidden border-r bg-card md:block">
        <div className="sticky top-0 h-screen flex flex-col">
          <div className="flex h-14 items-center px-4">
            <Link
              href="/projects"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              &larr; Back to Projects
            </Link>
          </div>
          <Separator />
          <div className="px-4 py-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Settings
            </p>
          </div>
          <nav className="px-2 space-y-1">
            {SETTINGS_NAV.map((item) => {
              const Icon = item.icon;
              const active =
                item.href === "/settings"
                  ? pathname === "/settings"
                  : pathname === item.href || pathname.startsWith(item.href + "/");
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
      </aside>

      {/* Main content */}
      <div className="flex flex-col">
        {/* Mobile header */}
        <header className="flex h-14 items-center border-b px-4 md:hidden">
          <Link
            href="/projects"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Projects
          </Link>
          <span className="ml-3 text-lg font-bold tracking-tight">Settings</span>
        </header>

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
