/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // destination: "http://103.90.224.132:8001/api/:path*",
         destination: "http://localhost:8001/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
