import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'www.flaticon.com',
        port: '',
        pathname: '/**', // อนุญาตให้ดึงรูปภาพจากทุก Path ของโดเมนนี้
      },
    ],
  },
};

export default nextConfig;
