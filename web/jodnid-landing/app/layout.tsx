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
  metadataBase: new URL("https://jodnid-home.vercel.app"),
  title: {
    default: "JodNid - จดบันทึกรายจ่ายง่ายๆ ผ่าน LINE AI",
    template: "%s | JodNid"
  },
  description: "เปลี่ยนการจดบัญชีให้เป็นเรื่องง่ายด้วย JodNid AI บน LINE แค่ส่งสลิปหรือพิมพ์บอก ระบบจะช่วยแยกหมวดหมู่และ VAT ให้อัตโนมัติ",
  openGraph: {
    title: "JodNid - จดบันทึกรายจ่ายผ่าน LINE AI",
    description: "จัดการการเงินของคุณได้ง่ายกว่าที่เคยผ่านแอป LINE",
    type: "website",
    locale: "th_TH",
  },
  alternates: {
    canonical: "/",
  }
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