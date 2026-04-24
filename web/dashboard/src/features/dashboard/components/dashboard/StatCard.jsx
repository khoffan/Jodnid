export const StatCard = ({ label, value, variant = "white" }) => {
  const isBlue = variant === "blue";

  return (
    <div
      className={`
        p-6 rounded-[2.5rem] shadow-sm border 
        ${
          isBlue
            ? "bg-indigo-600 text-white shadow-indigo-100 border-transparent"
            : "bg-white text-gray-800 border-gray-100"
        }
      `}
    >
      <div className="p-0">
        <p
          className={`
            text-[10px] font-medium uppercase tracking-wider
            ${isBlue ? "text-indigo-100/80" : "text-gray-400"}
          `}
        >
          {label}
        </p>
        <p className="text-2xl font-bold mt-1">฿{value.toLocaleString()}</p>
      </div>
    </div>
  );
};
