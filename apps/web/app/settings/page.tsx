import Link from "next/link";
import { Cpu } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure Atlas for your environment.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link href="/settings/models">
          <Card className="h-full cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-base">Models</CardTitle>
              </div>
              <CardDescription>
                Manage locally installed Ollama models, pull new ones, and
                configure inference profiles.
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>
    </div>
  );
}
