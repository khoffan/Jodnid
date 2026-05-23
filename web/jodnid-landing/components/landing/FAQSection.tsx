"use client";

import { FAQCategory } from "@/types/landing";
import React, { useState } from "react";

interface FAQSectionProps {
  faqData: FAQCategory[];
}

export const FAQSection: React.FC<FAQSectionProps> = ({ faqData }) => {
  // 2. State สำหรับเก็บว่าคำถามไหนกำลังถูกเปิดอยู่ (เก็บรูปแบบ "categoryIndex-itemIndex")
  const [openIndex, setOpenIndex] = useState<string | null>("0-0"); // เปิดอันแรกไว้เป็น Default


  const toggleFAQ = (catIndex: number, itemIndex: number) => {
    const targetIndex = `${catIndex}-${itemIndex}`;
    setOpenIndex(openIndex === targetIndex ? null : targetIndex);
  };

  return (
    <section className="bg-slate-50 py-20 px-4 sm:px-6 lg:px-8 min-h-screen font-sans">
      <div className="max-w-4xl mx-auto">
        {/* Header ส่วนหัวข้อ */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight mb-4">
            คำถามที่พบบ่อย 🤔
          </h2>
          <p className="text-base sm:text-lg text-slate-600 max-w-xl mx-auto">
            พบบรรดาข้อสงสัยและทุกคำตอบเกี่ยวกับ{" "}
            <span className="text-indigo-600 font-bold">JodNid</span>{" "}
            ผู้ช่วยจดบันทึกการเงินส่วนตัวของคุณ
          </p>
        </div>

        {/* FAQ Content Block */}
        <div className="space-y-12">
          {faqData.map((category, catIndex) => (
            <div key={category.id} className="space-y-4">
              {/* ชื่อหมวดหมู่ย่อย */}
              <div className="flex items-center space-x-2 pb-2 border-b border-slate-200">
                <span className="text-xl">{category.icon}</span>
                <h3 className="text-lg font-extrabold text-slate-800">{category.title}</h3>
              </div>

              {/* รายการคำถามภายในหมวดหมู่ */}
              <div className="space-y-3">
                {category.items.map((item, itemIndex) => {
                  const currentIndex = `${catIndex}-${itemIndex}`;
                  const isOpen = openIndex === currentIndex;

                  return (
                    <div
                      key={itemIndex}
                      className="bg-white rounded-2xl border border-slate-100 shadow-sm transition-all duration-300 overflow-hidden"
                    >
                      {/* ส่วนปุ่มกดถาม */}
                      <button
                        onClick={() => toggleFAQ(catIndex, itemIndex)}
                        className="w-full flex items-center justify-between p-5 text-left focus:outline-none group"
                        aria-expanded={isOpen}
                      >
                        <span className="text-sm sm:text-base font-black text-slate-800 group-hover:text-indigo-600 transition-colors duration-200 pr-4">
                          Q: {item.question}
                        </span>

                        {/* ไอคอน ลูกศร หมุนเมื่อกางออก */}
                        <div
                          className={`flex-shrink-0 w-6 h-6 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-500 transition-all duration-300 ${isOpen ? "transform rotate-180 bg-indigo-50 text-indigo-600" : ""}`}
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 9l-7 7-7-7"
                            />
                          </svg>
                        </div>
                      </button>

                      {/* ส่วนคำตอบ พร้อมทำ Animation Slide */}
                      <div
                        className={`transition-all duration-300 ease-in-out ${
                          isOpen ? "max-h-[500px] border-t border-slate-50" : "max-h-0"
                        } overflow-hidden`}
                      >
                        <div className="p-5 text-xs sm:text-sm text-slate-600 leading-relaxed bg-slate-50/50">
                          <strong className="text-indigo-600 font-bold block mb-1">A:</strong>
                          {item.answer}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* ส่วนท้าย - Call to Action (CTA) */}
        <div className="mt-16 text-center bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl p-8 sm:p-12 shadow-xl shadow-indigo-100 text-white">
          <h4 className="text-xl sm:text-2xl font-black mb-2">ยังมีข้อสงสัยด้านอื่นอยู่ใช่ไหม?</h4>
          <p className="text-sm text-indigo-100 mb-6 max-w-md mx-auto">
            ลองทักมาคุยกับ JodNid โดยตรงบน LINE
            เพื่อสัมผัสประสบการณ์จดบัญชีที่ง่ายที่สุดได้ทันทีครับ
          </p>
          <button className="bg-emerald-500 hover:bg-emerald-400 text-white font-black px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5 text-sm sm:text-base">
            💬 เพิ่มเพื่อนบน LINE เลย
          </button>
        </div>
      </div>
    </section>
  );
};
