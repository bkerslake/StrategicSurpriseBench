import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Strategic Surprise Bench",
  description:
    "An open benchmark for strategic warning under deception, uncertainty, and sudden change.",
  openGraph: {
    title: "Strategic Surprise Bench",
    description:
      "Can a model notice what matters in a fictional crisis without being told what reasoning to do?",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Strategic Surprise Bench",
    description:
      "Six fictional crises, neutral assessment prompts, and paired evidence updates.",
  },
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#f2efe8",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
