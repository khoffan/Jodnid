"use client";

import React from "react";
import { StepItem } from "@/types/landing";

const steps: StepItem[] = [
  {
    number: "01",
    title: "เพิ่มเพื่อนใน LINE",
    desc: "สแกน QR Code หรือกดปุ่มเพิ่มเพื่อน JodNid เพื่อเริ่มใช้งานได้ทันที ไม่ต้องสมัครสมาชิกให้วุ่นวาย",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
      </svg>
    ),
  },
  {
    number: "02",
    title: "ส่งสลิปหรือพิมพ์บอก",
    desc: "ถ่ายรูปสลิปธนาคารส่งเข้าแชท หรือพิมพ์ 'กินกาแฟ 120' AI ของเราจะประมวลผลและแยกยอด VAT ให้เอง",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
  },
  {
    number: "03",
    title: "ดูสรุปผลอัตโนมัติ",
    desc: "รับสรุปยอดรายวัน รายสัปดาห์ หรือคลิกดู Dashboard ส่วนตัวเพื่อวิเคราะห์พฤติกรรมการใช้เงินของคุณ",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
];

const HowItWorks: React.FC = () => {
  return (
    <section id="how-it-works" className="py-24 md:py-32 bg-white overflow-hidden">
      <div className="max-w-screen-xl mx-auto px-6 lg:px-12">
        {/* Section Header */}
        <div className="text-center mb-16 md:mb-20">
          <h2 className="text-4xl md:text-5xl font-black mb-5 tracking-tight text-slate-900">
            เริ่มใช้งานใน <span className="text-blue-600">3 ขั้นตอน</span>
          </h2>
          <p className="text-slate-500 text-lg max-w-2xl mx-auto leading-relaxed">
            ประหยัดเวลาการจดบัญชีได้มากกว่า 90% ด้วย Flow การทำงานที่ลื่นไหลที่สุดบน LINE
          </p>
        </div>

        <div className="relative">
          {/* Connecting Line (Desktop Only) */}
          <div className="hidden md:block absolute top-12 left-0 w-full h-[2px] bg-slate-100 -z-10" />

          <div className="grid md:grid-cols-3 gap-10 md:gap-12">
            {steps.map((step, idx) => (
              <div key={idx} className="relative flex flex-col items-center text-center group">
                {/* Step Number Badge */}
                <div className="w-24 h-24 bg-white border-4 border-slate-50 rounded-[2.5rem] shadow-xl shadow-slate-100 flex items-center justify-center mb-8 group-hover:border-blue-500 transition-all duration-300">
                  <div className="flex flex-col items-center">
                    <span className="text-blue-600 font-black text-2xl">{step.number}</span>
                    <div className="text-slate-300 mt-1">{step.icon}</div>
                  </div>
                </div>

                <h3 className="text-xl font-black mb-3 text-slate-900 group-hover:text-blue-600 transition-colors">
                  {step.title}
                </h3>
                <p className="text-slate-500 leading-relaxed max-w-xs text-sm md:text-base">
                  {step.desc}
                </p>

                {/* Arrow for Mobile (Optional Decor) */}
                {idx !== steps.length - 1 && (
                  <div className="md:hidden my-6 text-slate-200">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7-7-7" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA within Section */}
        <div className="mt-20 md:mt-24 p-10 md:p-14 bg-blue-600 rounded-[3rem] text-center text-white shadow-2xl shadow-blue-200 relative overflow-hidden">
          <div className="relative z-10 max-w-xl mx-auto">
            <h3 className="text-2xl md:text-3xl font-black mb-4">พร้อมจัดการเงินให้เป็นเรื่องง่ายหรือยัง?</h3>
            <p className="text-blue-100 mb-8 opacity-90 text-sm md:text-base leading-relaxed">
              เข้าร่วมกับผู้ใช้งานกว่าหลายร้อยคน ที่เปลี่ยนมาใช้ JodNid ช่วยจดบันทึกรายจ่ายรายวัน
            </p>
            <a
              href="https://line.me/R/ti/p/@256dlaen"
              className="inline-block bg-white text-blue-600 font-black py-4 px-10 rounded-2xl hover:bg-slate-50 transition-all active:scale-95 shadow-lg shadow-black/10"
            >
              เพิ่มเพื่อน JodNid เลยตอนนี้
            </a>
          </div>
          {/* Abstract Circle Decor */}
          <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute -left-10 -top-10 w-48 h-48 bg-blue-400/20 rounded-full blur-3xl" />
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;