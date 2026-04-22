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
    <nav className="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-lg border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 bg-green-500 rounded-2xl flex items-center justify-center text-white font-black text-xl shadow-lg shadow-green-200 group-hover:rotate-6 transition-transform">
            J
          </div>
          <span className="font-black text-2xl tracking-tighter text-slate-900">JodNid</span>
        </Link>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-10">
          {navLinks.map((link) => (
            <Link 
              key={link.href} 
              href={link.href} 
              className="text-sm font-bold text-slate-500 hover:text-green-600 transition-colors"
            >
              {link.label}
            </Link>
          ))}
          <Button size="sm" variant="line">เพิ่มเพื่อน</Button>
        </div>

        {/* Mobile Button (Simple Version) */}
        <div className="md:hidden">
          <Button size="sm" variant="line">เริ่มเลย</Button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;