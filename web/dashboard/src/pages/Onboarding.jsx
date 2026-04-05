
import { useState } from 'react';
import { useNavigate } from 'react-router';
import useTransactionStore from '../store/useTransectionStore';

const Onboarding = ({ userId }) => {
  const [budget, setBudget] = useState('');
  const { saveBudget, loading } = useTransactionStore();
  const navigate = useNavigate();

  const handleSave = async () => {
    if (!budget || budget <= 0) return alert("กรุณาระบุงบประมาณที่ถูกต้อง");
    
    const result = await saveBudget(userId, budget);
    console.log("Budget Save Result:", result);
    if (result.success) {
      // เมื่อบันทึกสำเร็จ ให้ส่งกลับไปหน้า Dashboard
      navigate('/');
    } else {
      alert("เกิดข้อผิดพลาด กรุณาลองใหม่");
      window.location.reload(); // รีโหลดหน้าเพื่อให้ผู้ใช้ลองใหม่อีกครั้ง (หรือจะใช้วิธีอื่นก็ได้ตามความเหมาะสม)
    }
  };

  return (
    <>
      <div className="flex-1 flex flex-col justify-center">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">ยินดีต้อนรับ! 👋</h1>
          <p className="text-gray-500 mt-2">เริ่มต้นใช้งาน "จดนิด" ด้วยการตั้งงบประมาณรายเดือนของคุณ</p>
        </div>

        <div className="space-y-6">
          <div>
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">งบประมาณเดือนนี้ (บาท)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="เช่น 15000"
              className="w-full text-4xl font-bold border-b-2 border-green-500 py-4 focus:outline-none placeholder:text-gray-200"
              autoFocus
            />
          </div>
          
          <div className="bg-green-50 p-4 rounded-2xl flex items-start gap-3">
            <span className="text-xl">💡</span>
            <p className="text-sm text-green-700">
              งบประมาณนี้จะช่วยให้คุณเห็นภาพรวมว่าเหลือเงินให้ใช้ได้อีกเท่าไหร่ในแต่ละเดือน
            </p>
          </div>
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={loading}
        className={`w-full py-4 rounded-2xl font-bold text-lg shadow-lg transition-all ${
          loading ? 'bg-gray-300' : 'bg-green-500 hover:bg-green-600 text-white active:scale-95'
        }`}
      >
        {loading ? 'กำลังบันทึก...' : 'เริ่มจดเลย!'}
      </button>
    </>
  );
};

export default Onboarding;