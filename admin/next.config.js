/** @type {import('next').NextConfig} */
const path = require('path');

const apiRewriteUrl = process.env.API_REWRITE_URL || 'http://localhost:8001/api/:path*';

const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: path.join(__dirname),
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: apiRewriteUrl
      }
    ]
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1',
    NEXT_PUBLIC_ADMIN_URL: process.env.NEXT_PUBLIC_ADMIN_URL || 'http://localhost:3002',
  },
}

module.exports = nextConfig
