"use client";

import React from "react";
import Link from "next/link";
import Button from "../ui/Button";
import { NavItem } from "@/types/landing";

const navLinks: NavItem[] = [
  { label: "ฟีเจอร์", href: "#features" },
  { label: "วิธีใช้งาน", href: "#how-it-works" },
  { label: "ราคา", href: "#pricing" },
];

const Navbar: React.FC = () => {
  return (
    <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100 shadow-sm">
      {/* ใช้ header ครอบส่วนหัวทั้งหมด และ nav สำหรับส่วนนำทาง */}
      <nav className="max-w-screen-xl mx-auto px-6 lg:px-12 h-16 md:h-20 flex items-center justify-between" aria-label="Main Navigation">

        {/* Logo - เพิ่ม title เพื่อบอก Google ว่าลิงก์นี้กลับหน้าหลัก */}
        <Link href="/" className="flex items-center gap-2.5 group" title="JodNid Home">
          <div className="w-9 h-9 md:w-10 md:h-10 bg-blue-600 rounded-2xl flex items-center justify-center text-white font-black text-lg md:text-xl shadow-lg shadow-blue-200 group-hover:rotate-6 transition-transform" aria-hidden="true">
            J
          </div>
          <span className="font-black text-xl md:text-2xl tracking-tighter text-slate-900">JodNid</span>
        </Link>

        {/* Desktop Links - ใช้ ul เพื่อโครงสร้างข้อมูลที่ถูกต้อง */}
        <div className="hidden md:flex items-center gap-8">
          <ul className="flex items-center gap-8 list-none">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="text-sm font-bold text-slate-500 hover:text-blue-600 transition-colors"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>

          {/* CTA Button */}
          <Button size="sm" variant="line">เพิ่มเพื่อน</Button>
        </div>

        {/* Mobile Button */}
        <div className="md:hidden">
          <Button size="sm" variant="line">เริ่มเลย</Button>
        </div>
      </nav>
    </header>
  );
};

export default Navbar;