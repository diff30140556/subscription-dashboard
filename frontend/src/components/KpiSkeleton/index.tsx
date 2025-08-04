import React from 'react';

interface KpiSkeletonProps {
  cardCount?: number;
}

const KpiSkeleton: React.FC<KpiSkeletonProps> = ({ cardCount = 4 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(cardCount)].map((_, index) => (
        <div key={index} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
          {/* Card title */}
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          {/* Main value */}
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          {/* Sparkline placeholder */}
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      ))}
    </div>
  );
};

export default KpiSkeleton;