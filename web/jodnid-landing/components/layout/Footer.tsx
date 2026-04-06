import React from "react";
import Link from "next/link";

const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-50 border-t border-slate-100 pt-20 pb-12">
      <div className="max-w-screen-xl mx-auto px-6 lg:px-12">
        <div className="grid md:grid-cols-4 gap-10 md:gap-12 mb-14">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold">J</div>
              <span className="font-black text-xl tracking-tighter text-slate-900">JodNid</span>
            </div>
            <p className="text-slate-500 max-w-xs leading-relaxed text-sm">
              ผู้ช่วยบันทึกรายจ่ายส่วนตัวผ่าน LINE ที่ฉลาดที่สุด{" "}
              จัดการเงินของคุณให้เป็นเรื่องง่ายในนิดเดียว
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-black mb-5 text-slate-900">เมนู</h4>
            <ul className="space-y-3 text-sm text-slate-500">
              <li><Link href="#features" className="hover:text-blue-600 transition-colors">ฟีเจอร์</Link></li>
              <li><Link href="#how-it-works" className="hover:text-blue-600 transition-colors">วิธีใช้งาน</Link></li>
              <li><Link href="#" className="hover:text-blue-600 transition-colors">นโยบายความเป็นส่วนตัว</Link></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-black mb-5 text-slate-900">ติดต่อเรา</h4>
            <ul className="space-y-3 text-sm text-slate-500">
              <li>LINE: @jodnid_ai</li>
              <li>Email: hello@jodnid.com</li>
              <li>Facebook: JodNid Project</li>
            </ul>
          </div>
        </div>

        <div className="pt-10 border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-slate-400">© 2026 JodNid. All rights reserved.</p>
          <div className="flex gap-4 text-xs text-slate-400">
            <span>Built by Typhoon LLM Tech</span>
            <span className="text-slate-200">|</span>
            <span>Design with ❤️ in Thailand</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;