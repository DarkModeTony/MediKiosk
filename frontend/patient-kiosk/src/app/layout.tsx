import { Inter } from "next/font/google";
import "./globals.css";
import { KioskSessionProvider } from "@/components/providers/KioskSessionProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "MediPlatform Kiosk",
  description: "Patient intake kiosk",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans`}>
        <KioskSessionProvider>
          {children}
        </KioskSessionProvider>
      </body>
    </html>
  );
}
