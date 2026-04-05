const TransactionDetail = ({ transaction }) => {
  return (
    <>
      <div className="p-6 border-b text-center">
        <h2 className="font-bold text-xl">รายละเอียดรายการ</h2>
      </div>
      
      <div className="p-6">
        <div className="flex justify-between mb-4">
          <span className="text-gray-500">รายการ</span>
          <span className="font-medium">{transaction.item_name}</span>
        </div>
        <div className="flex justify-between mb-4">
          <span className="text-gray-500">ยอดเงิน</span>
          <span className="font-bold text-red-500 text-xl">฿ {transaction.amount}</span>
        </div>
        
        {/* แสดงรูปสลิปจาก Path ที่เราเก็บไว้ */}
        {transaction.attachment_path && (
          <div className="mt-8">
            <p className="text-gray-500 mb-2">หลักฐานการทำรายการ</p>
            <img 
              src={`https://your-api.com/${transaction.attachment_path}`} 
              alt="Receipt" 
              className="w-full rounded-2xl shadow-md border"
            />
          </div>
        )}
      </div>
    </>
  );
};

export default TransactionDetail;