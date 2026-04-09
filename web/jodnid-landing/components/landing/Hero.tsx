
import React from "react";
import Button from "../ui/Button";

const Hero: React.FC = () => {
  return (
    // เปลี่ยนจาก div (ถ้ามีครอบอยู่ข้างนอก) เป็น main หรือใช้ section แบบที่คุณทำก็นับว่าดีแล้วครับ
    <section className="relative pt-24 pb-16 md:pt-36 md:pb-28 px-6 overflow-hidden bg-gradient-to-b from-blue-50/60 to-white">
      <div className="max-w-4xl mx-auto text-center relative z-10">

        {/* Badge: ใช้ span หรือ div ปกติถูกแล้วครับ */}
        <div className="inline-block px-4 py-1.5 mb-8 rounded-full bg-blue-100 text-blue-700 text-xs font-bold uppercase tracking-widest">
          The Smartest AI Bookkeeper
        </div>

        {/* Heading: h1 คือหัวใจของ SEO หน้าหลัก */}
        <h1 className="text-5xl md:text-7xl lg:text-8xl font-black mb-6 leading-[1.1] tracking-tight text-slate-900">
          {/* เพิ่มพิกัดคีย์เวิร์ด: "จดบันทึกรายรับรายจ่าย" หรือ "AI" ลงไปใน text (ถ้าปรับได้) */}
          จดบัญชีง่าย <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-blue-700">
            ผ่าน LINE Chat
          </span>
        </h1>

        {/* Sub-description: ใส่เนื้อหาที่บอทจะนำไปแสดงเป็น Snippet */}
        <p className="text-slate-500 text-lg md:text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
          {/* คีย์เวิร์ดสำคัญ: สแกนสลิป, แยก VAT, สรุปบัญชีอัตโนมัติ */}
          สแกนสลิป แยก VAT และทำสรุปบัญชีอัตโนมัติด้วย AI{" "}
          ไม่ต้องดาวน์โหลดแอปให้หนักเครื่อง
        </p>

        {/* CTA Buttons: สำหรับ SEO ปุ่มสำคัญควรมี title attribute อธิบายสั้นๆ */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button
            size="lg"
            variant="line"
            title="เพิ่มเพื่อน JodNid บน LINE เพื่อเริ่มจดบัญชี"
          >
            เพิ่มเพื่อนบน LINE
          </Button>
          <Button
            size="lg"
            variant="secondary"
            title="เรียนรู้วิธีการใช้งาน JodNid AI"
          >
            วิธีใช้งาน
          </Button>
        </div>
      </div>

      {/* Background Decor: ตรวจสอบว่ารูปประดับเหล่านี้มี aria-hidden="true" เพื่อไม่ให้รบกวนบอทอ่านเนื้อหา */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full -z-0 opacity-20 pointer-events-none" aria-hidden="true">
        {/* รูปประดับต่างๆ */}
      </div>
    </section>
  );
};

export default Hero;