import { SidebarNav } from "@/components/sidebar-nav";
import { MobileNav } from "@/components/mobile-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen md:grid-cols-[220px_1fr]">
      {/* Desktop sidebar */}
      <aside className="hidden border-r bg-card md:block">
        <div className="sticky top-0 h-screen">
          <SidebarNav />
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-col">
        {/* Mobile header */}
        <header className="flex h-14 items-center border-b px-4 md:hidden">
          <MobileNav />
          <span className="ml-2 text-lg font-bold tracking-tight">Atlas</span>
        </header>

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
