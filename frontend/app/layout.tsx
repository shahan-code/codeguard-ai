import type { Metadata } from "next";
import "./globals.css";

// NOTE (documented deviation): the original design called for Space Grotesk /
// Inter / IBM Plex Mono via next/font/google. Some build environments (e.g.
// network-restricted CI/sandboxes) cannot reach fonts.googleapis.com at build
// time, which makes `next/font/google` fail the build entirely. To keep the
// project reliably buildable everywhere, we define the same three type roles
// (display / body / mono) as CSS custom properties backed by system font
// stacks. If you have build-time internet access, swapping these for
// next/font/google is a drop-in upgrade — see README "Future Improvements".

export const metadata: Metadata = {
  title: "CodeGuard AI",
  description: "Find risky code before it becomes a bug.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body">{children}</body>
    </html>
  );
}
