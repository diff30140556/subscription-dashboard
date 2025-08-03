'use client';

import { useEffect, useState } from 'react';

export default function SimpleHome() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div>Loading...</div>;
  }

  return (
    <main className="p-4">
      <h1 className="text-2xl font-bold mb-4">Simple Test Page</h1>
      <p>This is a test to isolate hydration issues.</p>
      <div className="mt-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-lg border p-4">
            <div className="text-sm text-gray-500">Test Metric 1</div>
            <div className="text-2xl font-bold mt-1">26.5%</div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="text-sm text-gray-500">Test Metric 2</div>
            <div className="text-2xl font-bold mt-1">32.4</div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="text-sm text-gray-500">Test Metric 3</div>
            <div className="text-2xl font-bold mt-1">64.8</div>
          </div>
        </div>
      </div>
    </main>
  );
}