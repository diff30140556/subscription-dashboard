import React from 'react';

interface LoadingSkeletonProps {
  title?: string;
  rows?: number;
  hasChart?: boolean;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  title = "Loading...", 
  rows = 3,
  hasChart = true 
}) => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Title skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-8 bg-gray-200 rounded w-64"></div>
      </div>
      
      {/* Chart area skeleton */}
      {hasChart && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="h-80 bg-gray-100 rounded-lg"></div>
        </div>
      )}
      
      {/* Content rows skeleton */}
      <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LoadingSkeleton;