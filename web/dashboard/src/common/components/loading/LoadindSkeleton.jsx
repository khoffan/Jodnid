export default function LoadingSkeleton() {
  return (
    <div className="p-6 space-y-8 animate-pulse">
      {/* 1. Header Skeleton */}
      <div className="flex justify-between items-center">
        <div className="h-8 w-48 bg-gray-200 rounded-md"></div>
        <div className="h-10 w-32 bg-gray-200 rounded-lg"></div>
      </div>

      {/* 2. Stats Cards Skeleton (4 Columns) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-4 border border-gray-100 rounded-xl bg-white shadow-sm space-y-3">
            <div className="h-4 w-24 bg-gray-200 rounded"></div>
            <div className="h-8 w-16 bg-gray-300 rounded"></div>
            <div className="h-3 w-32 bg-gray-100 rounded"></div>
          </div>
        ))}
      </div>

      {/* 3. Main Content Area (Chart + Recent Activity) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Large Chart Skeleton */}
        <div className="lg:col-span-2 h-64 bg-gray-50 border border-gray-100 rounded-xl p-4">
          <div className="h-6 w-40 bg-gray-200 rounded mb-4"></div>
          <div className="w-full h-40 bg-gray-200 rounded-lg opacity-50"></div>
        </div>

        {/* List Skeleton */}
        <div className="h-64 bg-white border border-gray-100 rounded-xl p-4 space-y-4">
          <div className="h-6 w-32 bg-gray-200 rounded"></div>
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center space-x-3">
              <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-3 w-full bg-gray-200 rounded"></div>
                <div className="h-3 w-2/3 bg-gray-100 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Table Skeleton */}
      <div className="space-y-4">
        <div className="h-6 w-44 bg-gray-200 rounded"></div>
        <div className="border border-gray-100 rounded-xl overflow-hidden">
          <div className="h-12 bg-gray-50 border-b border-gray-100"></div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-white border-b border-gray-50 px-4 flex items-center">
               <div className="h-4 w-full bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}