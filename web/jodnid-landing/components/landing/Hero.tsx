
import React from "react";
import Button from "../ui/Button";

const Hero: React.FC = () => {
  return (
    <section className="relative pt-24 pb-16 md:pt-36 md:pb-28 px-6 overflow-hidden bg-gradient-to-b from-blue-50/60 to-white">
      <div className="max-w-4xl mx-auto text-center relative z-10">
        {/* Badge */}
        <div className="inline-block px-4 py-1.5 mb-8 rounded-full bg-blue-100 text-blue-700 text-xs font-bold uppercase tracking-widest">
          The Smartest AI Bookkeeper
        </div>

        {/* Heading */}
        <h1 className="text-5xl md:text-7xl lg:text-8xl font-black mb-6 leading-[1.1] tracking-tight text-slate-900">
          จดบัญชีง่าย <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-blue-700">
            ผ่าน LINE Chat
          </span>
        </h1>

        {/* Sub-description */}
        <p className="text-slate-500 text-lg md:text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
          สแกนสลิป แยก VAT และทำสรุปบัญชีอัตโนมัติด้วย AI{" "}
          ไม่ต้องดาวน์โหลดแอปให้หนักเครื่อง
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button size="lg" variant="line">เพิ่มเพื่อนบน LINE</Button>
          <Button size="lg" variant="secondary">วิธีใช้งาน</Button>
        </div>
      </div>
    </section>
  );
};

export default Hero;