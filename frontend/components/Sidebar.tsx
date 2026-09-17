"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analyze", label: "Analyze" },
  { href: "/history", label: "History" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="flex h-screen w-56 flex-col justify-between border-r border-ink-700 bg-ink-900 px-4 py-6">
      <div>
        <Link href="/dashboard" className="mb-8 flex items-center gap-2 px-2">
          <span className="h-2 w-2 rounded-full bg-signal-500" />
          <span className="font-display text-[15px] font-semibold text-mist-50">CodeGuard AI</span>
        </Link>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-3 py-2 text-sm transition-colors ${
                  active ? "bg-ink-700 text-mist-50" : "text-mist-300 hover:bg-ink-800 hover:text-mist-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
      <button
        onClick={() => {
          clearToken();
          router.push("/login");
        }}
        className="rounded-md px-3 py-2 text-left text-sm text-mist-400 hover:bg-ink-800 hover:text-mist-100"
      >
        Sign out
      </button>
    </aside>
  );
}
