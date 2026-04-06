import Link from "next/link";
import { ProjectsSidebarNav } from "@/components/projects/projects-sidebar-nav";
import { ProjectsMobileNav } from "@/components/projects/projects-mobile-nav";

export default function ProjectsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen md:grid-cols-[220px_1fr]">
      {/* Desktop sidebar */}
      <aside className="hidden border-r bg-card md:block">
        <div className="sticky top-0 h-screen">
          <ProjectsSidebarNav />
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-col">
        {/* Mobile header */}
        <header className="flex h-14 items-center border-b px-4 md:hidden">
          <ProjectsMobileNav />
          <Link href="/projects" className="ml-2 text-lg font-bold tracking-tight">
            Atlas
          </Link>
        </header>

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
