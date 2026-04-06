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
    color: "bg-blue-50 text-blue-500",
  },
  {
    title: "สรุปผลรายเดือน",
    desc: "ดูรายงานการใช้จ่ายแยกตามหมวดหมู่ได้ชัดเจน ช่วยให้คุณวางแผนการเงินได้ดีขึ้น",
    icon: "📊",
    color: "bg-indigo-50 text-indigo-500",
  },
];

const Features: React.FC = () => {
  return (
    <section id="features" className="py-24 md:py-32 bg-white">
      <div className="max-w-screen-xl mx-auto px-6 lg:px-12">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-5 tracking-tight text-slate-900">
            ฉลาดกว่าเดิม <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-blue-700">
              ด้วยพลัง AI ส่วนตัว
            </span>
          </h2>
          <p className="text-slate-500 text-lg leading-relaxed">
            ลืมการจดบัญชีแบบเดิมๆ ไปได้เลย JodNid ออกแบบมาเพื่อคนยุคใหม่ที่ต้องการความเร็วและแม่นยำ
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-6 md:gap-8 mb-16 md:mb-20">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="p-8 md:p-10 rounded-[2.5rem] bg-slate-50 border border-slate-100 hover:shadow-2xl hover:shadow-slate-200 transition-all group"
            >
              <div
                className={`w-14 h-14 ${feature.color} rounded-2xl flex items-center justify-center text-2xl mb-6 group-hover:scale-110 transition-transform`}
              >
                {feature.icon}
              </div>
              <h3 className="text-xl font-black mb-3 text-slate-900">{feature.title}</h3>
              <p className="text-slate-500 leading-relaxed text-sm md:text-base">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Highlight Section with Mockup */}
        <div className="bg-slate-900 rounded-[3rem] p-10 md:p-16 lg:p-20 overflow-hidden relative flex flex-col md:flex-row items-center gap-12 md:gap-16 shadow-2xl">
          <div className="flex-1 relative z-10">
            <span className="text-blue-400 font-black text-xs uppercase tracking-widest mb-4 block">
              Highlight Feature
            </span>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-black text-white mb-6 leading-tight">
              แยกภาษี (VAT) <br /> ให้อัตโนมัติ!
            </h2>
            <p className="text-slate-400 text-base md:text-lg mb-8 leading-relaxed max-w-sm">
              JodNid ไม่ได้อ่านแค่ยอดรวม แต่เราสกัดข้อมูลยอดก่อนภาษีและ VAT 7%{" "}
              เพื่อให้คุณเห็นต้นทุนแฝงและจัดการภาษีได้อย่างมืออาชีพ
            </p>
            <div className="flex gap-4 flex-wrap">
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm min-w-[100px]">
                <p className="text-white font-bold mb-1">99.9%</p>
                <p className="text-slate-500 text-xs text-nowrap">ความแม่นยำของ AI</p>
              </div>
              <div className="p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm min-w-[110px]">
                <p className="text-white font-bold mb-1">&lt; 2 วินาที</p>
                <p className="text-slate-500 text-xs text-nowrap">ความเร็วในการสแกน</p>
              </div>
            </div>
          </div>

          <div className="flex-1 w-full flex justify-center relative">
            {/* วาง ChatMockup ที่เราสร้างไว้ก่อนหน้า */}
            <ChatMockup />
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-blue-500/20 rounded-full blur-[100px] -z-10" />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;