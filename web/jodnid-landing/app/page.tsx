import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWork from "@/components/landing/HowItWork";
import { FAQSection } from "@/components/landing/FAQSection";
import { FAQCategory, FAQItem } from "@/types/landing";

export default function Home() {
  const faqData: FAQCategory[] = [
    {
      id: "general",
      title: "การใช้งานทั่วไป",
      icon: "📱",
      items: [
        {
          question: "JodNid (จดนิด) คืออะไร?",
          answer:
            "JodNid คือผู้ช่วยบันทึกรายรับ-รายจ่ายส่วนตัวอัจฉริยะผ่าน LINE Application โดยที่คุณไม่ต้องดาวน์โหลดแอปพลิเคชันอื่นเพิ่ม เพียงแค่พิมพ์ข้อความ ส่งสลิป หรือส่งเสียงบอก บอทของเราจะจัดการบันทึกและจำแนกหมวดหมู่ให้คุณทันทีภายในไม่กี่วินาที",
        },
        {
          question: "ต้องสมัครใช้งานอย่างไร เสียเงินไหม?",
          answer:
            "เริ่มต้นใช้งานได้ฟรีง่ายๆ เพียงแค่เพิ่มเพื่อน (Add Friend) กับ JodNid บน LINE จากนั้นคุณสามารถเริ่มพิมพ์บันทึกก้าวแรกได้ทันทีโดยไม่ต้องกรอกข้อมูลส่วนตัวหรือผูกบัญชีธนาคารใดๆ ให้ยุ่งยากครับ",
        },
      ],
    },
    {
      id: "ai-features",
      title: "ฟีเจอร์และการทำงานของ AI",
      icon: "🤖",
      items: [
        {
          question: "พิมพ์บอก JodNid แบบไหนได้บ้าง?",
          answer:
            'พิมพ์ได้อย่างอิสระเหมือนคุยกับเพื่อนเลยครับ เช่น "กินกะเพราไก่ไข่ดาว 60 บาท", "ซื้อกาแฟไป 120", หรือ "เงินเดือนออก 35,000" ระบบ AI ของเราฉลาดพอที่จะแยกแยะได้เองว่าเป็นรายรับหรือรายจ่าย และวิเคราะห์หมวดหมู่ให้เสร็จสรรพ',
        },
        {
          question: 'ส่งรูปภาพ "สลิปโอนเงิน" ให้ช่วยจดได้ไหม?',
          answer:
            "ได้แน่นอนครับ! JodNid มีระบบ OCR และ AI อัจฉริยะ เพียงคุณส่งรูปสลิปธนาคารเข้ามา ระบบจะช่วยอ่านชื่อร้าน ยอดเงิน และวิเคราะห์หมวดหมู่รายจ่ายให้อัตโนมัติ พร้อมส่งการ์ดสรุปกลับไปให้คุณตรวจสอบความถูกต้องทันที",
        },
        {
          question: "ถ้า AI วิเคราะห์หมวดหมู่หรือยอดเงินผิดพลาด ต้องทำอย่างไร?",
          answer:
            "ทุกครั้งที่ JodNid บันทึกรายการ ระบบจะส่งการ์ดรายการ (Flex Message) กลับไปให้คุณตรวจสอบ หากมีรายการขยะ (เช่น VAT หรือ ยอดโอนซ้ำ) หรือหมวดหมู่ไม่ตรงใจ คุณสามารถกดปุ่มลบ (🗑️) หรือแก้ไขรายการได้ทันทีจากหน้าแชท LINE โดยไม่ต้องสลับแอปไปมา",
        },
      ],
    },
    {
      id: "dashboard",
      title: "งบประมาณและรายงาน",
      icon: "📊",
      items: [
        {
          question: "สามารถตั้งงบประมาณ (Budget) เพื่อควบคุมค่าใช้จ่ายได้ไหม?",
          answer:
            "ได้ครับ คุณสามารถตั้งงบประมาณแยกตามหมวดหมู่ได้ (เช่น งบค่าอาหาร, งบช้อปปิ้ง) และทุกครั้งที่คุณบันทึกรายจ่าย JodNid จะช่วยหักยอดเงินจากงบนั้นๆ พร้อมแจ้งเตือนทันทีหากงบของคุณใกล้จะเต็ม",
        },
        {
          question: "สามารถดูรายงานสรุปยอดเงินย้อนหลังได้ที่ไหน?",
          answer:
            "คุณสามารถกดดูรายงานสรุปแบบสวยงามผ่าน LIFF (LINE Front-end Framework) ได้ทันทีจากในแชท LINE ซึ่งจะแสดงกราฟวงกลมแยกหมวดหมู่ และประวัติการใช้เงินอย่างละเอียด ช่วยให้คุณวางแผนการเงินได้มีประสิทธิภาพมากขึ้น",
        },
      ],
    },
    {
      id: "privacy",
      title: "ความปลอดภัยและความเป็นส่วนตัว",
      icon: "🔒",
      items: [
        {
          question: "ข้อมูลการเงินของฉันปลอดภัยแค่ไหน?",
          answer:
            "ข้อมูลทั้งหมดถูกจัดเก็บและประมวลผลด้วยสถาปัตยกรรมซอฟต์แวร์ที่แน่นหนา (Clean Architecture) ข้อมูลธุรกรรมและสลิปของคุณจะถูกใช้เพื่อการวิเคราะห์และสรุปผลส่วนตัวของคุณเท่านั้น เราไม่มีนโยบายนำข้อมูลทางการเงินไปเผยแพร่หรือขายให้แก่บุคคลภายนอกเด็ดขาด",
        },
      ],
    },
  ];

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqData.flatMap((category) =>
      category.items.map((item: FAQItem) => ({
        "@type": "Question",
        name: item.question,
        acceptedAnswer: {
          "@type": "Answer",
          text: item.answer,
        },
      })),
    ),
  };

  return (
    <main className="flex flex-col w-full">
      <Hero />
      <Features />
      <HowItWork />
      <FAQSection faqData={faqData} />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </main>
  );
}
