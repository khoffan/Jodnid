import React, { useEffect } from 'react';
import useTransactionStore from '../store/useTransectionStore';

const Dashboard = ({ userId }) => {
  const { transactions, totalAmount, summary, fetchDashboard, loading } = useTransactionStore();

  useEffect(() => {
    if (userId) fetchDashboard(userId);
  }, [userId]);

  if (loading) return <div className="p-10 text-center">กำลังโหลดข้อมูล...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-20">
      {/* Header Card */}
      <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-3xl p-6 text-white shadow-lg mb-6">
        <p className="opacity-80 text-sm">ยอดใช้จ่ายเดือนนี้</p>
        <h1 className="text-4xl font-bold mt-1">฿ {totalAmount.toLocaleString()}</h1>
      </div>

      {/* Category Summary (Simple Grid) */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {Object.entries(summary).map(([name, amount]) => (
          <div key={name} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
            <p className="text-gray-500 text-xs">{name}</p>
            <p className="font-bold text-gray-800">฿ {amount.toLocaleString()}</p>
          </div>
        ))}
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-3xl p-5 shadow-sm border border-gray-100">
        <h3 className="font-bold text-gray-800 mb-4">รายการล่าสุด</h3>
        <div className="space-y-4">
          {transactions.map((tx, idx) => (
            <div key={idx} className="flex items-center justify-between border-b border-gray-50 pb-3 last:border-0">
              <div className="flex items-center gap-3">
                <div className="bg-gray-100 w-10 h-10 rounded-full flex items-center justify-center text-xl">
                  {tx.icon}
                </div>
                <div>
                  <p className="font-medium text-gray-800 leading-none">{tx.item}</p>
                  <p className="text-gray-400 text-[10px] mt-1">{tx.date}</p>
                </div>
              </div>
              <p className="font-bold text-red-500">-฿ {tx.amount}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;