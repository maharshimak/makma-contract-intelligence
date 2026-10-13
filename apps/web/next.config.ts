import type { NextConfig } from "next";
const production=process.env.NODE_ENV==="production";
const apiOrigin=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";
const securityHeaders=[
  {key:"X-Content-Type-Options",value:"nosniff"},
  {key:"Referrer-Policy",value:"strict-origin-when-cross-origin"},
  {key:"Permissions-Policy",value:"camera=(), microphone=(), geolocation=()"},
  {key:"X-Frame-Options",value:"DENY"},
  ...(production?[{key:"Strict-Transport-Security",value:"max-age=31536000; includeSubDomains"},{key:"Content-Security-Policy",value:`default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ${apiOrigin}; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`}]:[]),
];
const nextConfig: NextConfig = {
  output: "standalone",
  distDir: process.env.NEXT_BUILD_DIR ?? ".next",
  async headers(){return [{source:"/(.*)",headers:securityHeaders}]},
};
export default nextConfig;
