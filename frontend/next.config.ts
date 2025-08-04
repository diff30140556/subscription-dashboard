import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,

  eslint: {
    // need to remove
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;