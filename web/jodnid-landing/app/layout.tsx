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
  description: "แอปผู้ช่วยจดบันทึกรายจ่ายอัตโนมัติผ่าน LINE ใช้ AI วิเคราะห์สลิปธนาคารและข้อความ สะดวก รวดเร็ว แม่นยำ",
  keywords: ["จดบันทึกรายจ่าย", "แอปรายรับรายจ่าย", "AI สแกนสลิป", "LINE Bot รายรับรายจ่าย", "Jodnid", "jodnid", "jod", "Jod", "จดนิ๊ด", "จดนิด", "จดนิ๊ดนึง", "จดนิดนึง", "จดนิ๊ดเดียว", "จดนิดเดียว", "จดนิ๊ดเดียวพอ", "จดนิดเดียวพอ"],
  authors: [{ name: "Khoffan Leemanan" }],
  openGraph: {
    title: "JodNid - จดบันทึกรายจ่ายผ่าน LINE AI",
    description: "จัดการการเงินของคุณได้ง่ายกว่าที่เคยผ่านแอป LINE",
    type: "website",
    locale: "th_TH",
    url: "https://jodnid-home.vercel.app",
    siteName: "JodNid",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
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