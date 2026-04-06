import type { Metadata } from "next";
import { IBM_Plex_Sans_Thai } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";

const thaiFont = IBM_Plex_Sans_Thai({
  subsets: ["thai"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "JodNid - จดบันทึกรายจ่ายง่ายๆ ผ่าน LINE AI",
  description: "สแกนสลิป แยก VAT และทำสรุปบัญชีอัตโนมัติด้วยพลัง AI",
  openGraph: {
    title: "JodNid - จดง่าย นิดเดียว",
    description: "จัดการเงินผ่าน LINE ไม่ต้องโหลดแอปเพิ่ม",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="th" className={thaiFont.className}>
      <body className="bg-white text-slate-900 antialiased">
        <Navbar />
        <main className="pt-16 md:pt-20">{children}</main>
        <Footer />
      </body>
    </html>
  );
}