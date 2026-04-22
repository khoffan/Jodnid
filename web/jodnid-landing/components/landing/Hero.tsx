import React from "react";
import Button from "../ui/Button";

const Hero: React.FC = () => {
  return (
    <section className="relative pt-20 pb-16 px-6 overflow-hidden bg-linear-to-b from-green-100/50 to-white">
      <div className="max-w-5xl mx-auto text-center relative z-10">
        <div className="inline-block px-4 py-1.5 mt-6 mb-6 rounded-full bg-green-100 text-green-700 text-xs font-bold uppercase tracking-widest">
          The Smartest AI Bookkeeper
        </div>
        <h1 className="text-5xl md:text-8xl font-black mb-8 leading-[1.1] tracking-tight">
          จดบัญชีง่าย ๆ <br />
          <span className="text-transparent bg-clip-text bg-linear-to-r from-green-500 to-green-700">ผ่าน LINE Chat</span>
        </h1>
        <p className="text-gray-500 text-lg md:text-xl mb-10 max-w-2xl mx-auto">
          สแกนสลิปและทำสรุปบัญชีอัตโนมัติด้วย AI
          ไม่ต้องดาวน์โหลดแอปให้หนักเครื่อง
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button size="lg" variant="line">เพิ่มเพื่อนบน LINE</Button>
          <Button size="lg" variant="secondary" navigate="#how-it-works">วิธีใช้งาน</Button>
        </div>
      </div>
    </section>
  );
};

export default Hero;