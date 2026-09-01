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
      "Can a model keep several explanations alive, buy the right evidence, and act before the obvious story falls apart?",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Strategic Surprise Bench",
    description:
      "Six closed-world cases for strategic warning, collection, forecasting, and policy choice.",
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
