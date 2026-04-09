import React from "react";
import Link from "next/link";

const Footer: React.FC = () => {
  return (
    // tag <footer> เหมาะสมที่สุดแล้วครับ
    <footer className="bg-slate-50 border-t border-slate-100 pt-20 pb-12">
      <div className="max-w-screen-xl mx-auto px-6 lg:px-12">
        <div className="grid md:grid-cols-4 gap-10 md:gap-12 mb-14">

          {/* Brand & Description */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold" aria-hidden="true">J</div>
              {/* ใช้ span หรือ p แทน h ที่นี่ เพื่อไม่ให้ไปกวนลำดับ h1-h3 ของเนื้อหาหลัก */}
              <span className="font-black text-xl tracking-tighter text-slate-900">JodNid</span>
            </div>
            <p className="text-slate-500 max-w-xs leading-relaxed text-sm">
              {/* เพิ่มคีย์เวิร์ด: AI จดบัญชี, บันทึกรายจ่ายอัตโนมัติ */}
              JodNid คือผู้ช่วยบันทึกรายจ่ายส่วนตัวผ่าน LINE AI ที่ฉลาดที่สุด
              ช่วยคุณสแกนสลิปและจัดการเงินให้เป็นเรื่องง่ายในนิดเดียว
            </p>
          </div>

          {/* Navigation Links */}
          <nav> {/* ครอบด้วย nav เพื่อบอกว่าเป็นเมนูนำทางสำรอง */}
            <h4 className="font-black mb-5 text-slate-900">เมนู</h4>
            <ul className="space-y-3 text-sm text-slate-500">
              <li>
                <Link href="#features" className="hover:text-blue-600 transition-colors" title="ดูฟีเจอร์ทั้งหมดของ JodNid">
                  ฟีเจอร์
                </Link>
              </li>
              <li>
                <Link href="#how-it-works" className="hover:text-blue-600 transition-colors" title="ขั้นตอนการใช้งาน JodNid">
                  วิธีใช้งาน
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-blue-600 transition-colors" title="อ่านนโยบายความเป็นส่วนตัว">
                  นโยบายความเป็นส่วนตัว
                </Link>
              </li>
            </ul>
          </nav>

          {/* Contact Information */}
          {/* ใช้ tag <address> สำหรับข้อมูลติดต่อ (Good for SEO) */}
          <address className="not-italic">
            <h4 className="font-black mb-5 text-slate-900">ติดต่อเรา</h4>
            <ul className="space-y-3 text-sm text-slate-500">
              <li>
                <a href="https://line.me/R/ti/p/@jodnid_ai" className="hover:text-blue-600 transition-colors">
                  LINE: @jodnid_ai
                </a>
              </li>
              <li>
                <a href="mailto:hello@jodnid.com" className="hover:text-blue-600 transition-colors">
                  Email: hello@jodnid.com
                </a>
              </li>
              <li>
                <a href="https://facebook.com/jodnid" className="hover:text-blue-600 transition-colors">
                  Facebook: JodNid Project
                </a>
              </li>
            </ul>
          </address>
        </div>

        {/* Bottom Bar */}
        <div className="pt-10 border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] md:text-xs text-slate-400">
          <p>© 2026 JodNid. All rights reserved.</p>
          <div className="flex gap-4 items-center">
            {/* การระบุเทคโนโลยีที่ใช้ (Typhoon LLM) ช่วยเสริมความน่าเชื่อถือด้าน Expertise */}
            <span>Powered by <strong>Typhoon LLM</strong></span>
            <span className="text-slate-200" aria-hidden="true">|</span>
            <span>Design with ❤️ in Thailand</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;