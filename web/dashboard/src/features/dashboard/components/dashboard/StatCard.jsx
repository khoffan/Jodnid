export const StatCard = ({ label, value, variant = "white" }) => {
  const isBlue = variant === "blue";
  return (
    <div className={`${isBlue ? "bg-indigo-600 text-white shadow-indigo-100" : "bg-white text-gray-800 border-gray-100"} p-6 rounded-[2.5rem] shadow-sm border`}>
      <p className={`${isBlue ? "text-indigo-100 opacity-80" : "text-gray-400"} text-[10px] font-medium uppercase`}>
        {label}
      </p>
      <p className="text-2xl font-bold mt-1">
        ฿{value.toLocaleString()}
      </p>
    </div>
  );
};