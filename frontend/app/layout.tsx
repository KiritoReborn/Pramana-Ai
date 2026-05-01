import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pramana AI Procurement Platform",
  description: "Government procurement platform frontend for RBAC workflows."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
