import React from "react";
import ChatMockup from "./ChatMockup";
import { FeatureItem } from "@/types/landing";

const features: FeatureItem[] = [
  {
    title: "สแกนสลิปอัจฉริยะ",
    desc: "ส่งรูปสลิปธนาคารเข้า LINE AI จะอ่านยอดเงินและแยก VAT ให้ทันทีไม่ต้องพิมพ์เอง",
    icon: "📸",
    color: "bg-blue-50 text-blue-600",
  },
  {
    title: "จดด้วยเสียงหรือข้อความ",
    desc: "พิมพ์บอกเหมือนคุยกับเพื่อน 'กินกะเพราไป 60 บาท' ระบบจะบันทึกและจัดหมวดหมู่ให้เอง",
    icon: "💬",
    color: "bg-green-50 text-green-600",
  },
  {
    title: "สรุปผลรายเดือน",
    desc: "ดูรายงานการใช้จ่ายแยกตามหมวดหมู่ได้ชัดเจน ช่วยให้คุณวางแผนการเงินได้ดีขึ้น",
    icon: "📊",
    color: "bg-purple-50 text-purple-600",
  },
];

const Features: React.FC = () => {
  return (
    <section id="features" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-4xl md:text-6xl text-black font-bold mb-6 tracking-tight">
            ฉลาดกว่าเดิม <br />
            <span className="text-green-500 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-600">ด้วยพลัง AI ส่วนตัว</span>
          </h2>
          <p className="text-slate-500 text-lg">
            ลืมการจดบัญชีแบบเดิมๆ ไปได้เลย JodNid ออกแบบมาเพื่อคนยุคใหม่ที่ต้องการความเร็วและแม่นยำ
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-8 mb-32">
          {features.map((feature, idx) => (
            <div key={idx} className="p-10 rounded-[3rem] bg-slate-50 border border-slate-100 hover:shadow-2xl hover:shadow-slate-200 transition-all group">
              <div className={`w-16 h-16 ${feature.color} rounded-[1.5rem] flex items-center justify-center text-3xl mb-8 group-hover:scale-110 transition-transform`}>
                {feature.icon}
              </div>
              <h3 className="text-2xl text-black font-bold mb-4">{feature.title}</h3>
              <p className="text-slate-500 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Highlight Section with Mockup */}
        <div className="bg-slate-900 rounded-[4rem] p-12 md:p-20 overflow-hidden relative flex flex-col md:flex-row items-center gap-16 shadow-2xl">
          <div className="flex-1 relative z-10">
            <span className="text-green-400 font-black text-sm uppercase tracking-widest mb-6 block">Highlight Feature</span>
            <h2 className="text-4xl md:text-6xl font-black text-white mb-8 leading-tight">
              เปลี่ยนภาพถ่ายใบเสร็จให้กลายเป็นข้อมูลบัญชีที่ทรงพลัง ด้วยพลังของ AI ระดับโลก
            </h2>
            <p className="text-slate-400 text-lg mb-10 leading-relaxed">
              เทคโนโลยี OCR ที่แม่นยำสูง อ่านข้อมูลจากใบเสร็จทุกรูปแบบ ไม่ว่าจะเป็นใบเสร็จร้านค้าทั่วไป หรือใบเสร็จจากธนาคาร
            </p>
            <div className="flex gap-4">
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm">
                <p className="text-white font-bold mb-1">99.9%</p>
                <p className="text-white-300 text-xs text-nowrap">ความแม่นยำของ AI</p>
              </div>
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm">
                <p className="text-white font-bold mb-1">&lt; 2 วินาที</p>
                <p className="text-white-300 text-xs text-nowrap">ความเร็วในการสแกน</p>
              </div>
            </div>
          </div>

          <div className="flex-1 w-full flex justify-center relative">
            {/* วาง ChatMockup ที่เราสร้างไว้ก่อนหน้า */}
            <ChatMockup />
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-green-500/20 rounded-full blur-[100px] -z-10" />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;