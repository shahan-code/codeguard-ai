"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthed } from "@/lib/api";
import Sidebar from "@/components/Sidebar";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isAuthed()) {
      router.replace("/login");
    } else {
      setChecked(true);
    }
  }, [router]);

  if (!checked) {
    return <div className="flex h-screen items-center justify-center text-mist-400">Loading…</div>;
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="min-h-screen flex-1 bg-ink-950 px-10 py-8">{children}</main>
    </div>
  );
}
