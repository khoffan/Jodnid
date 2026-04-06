import React from "react";

const ChatMockup: React.FC = () => {
  return (
    <div className="bg-[#7494C4] rounded-[3rem] p-5 shadow-2xl border-[10px] border-slate-900 aspect-[9/18] w-full max-w-[320px] mx-auto">
      {/* LINE Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 bg-green-500 rounded-full flex items-center justify-center text-white font-bold text-xs">J</div>
        <div className="text-white text-[11px] font-bold">JodNid AI Bot</div>
      </div>

      {/* Message Area */}
      <div className="space-y-4">
        <div className="flex justify-end">
          <div className="w-28 h-36 bg-white/20 rounded-2xl border-2 border-white/40 flex items-center justify-center text-[10px] text-white">📷 Slip Image</div>
        </div>
        
        <div className="flex justify-start">
          <div className="bg-white rounded-2xl rounded-tl-none p-4 shadow-sm">
            <p className="text-[11px] font-black text-green-600 mb-2 italic">✨ วิเคราะห์สลิปสำเร็จ!</p>
            <div className="text-[10px] text-slate-700 space-y-1">
              <p>💰 ยอดอาหาร: ฿180.00</p>
              <p>🧾 VAT (7%): ฿12.60</p>
              <hr className="my-1 border-slate-100" />
              <p className="font-black text-slate-900">รวมทั้งสิ้น: ฿192.60</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMockup;