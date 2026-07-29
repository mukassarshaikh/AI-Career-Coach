/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow images from Cloudinary
  images: {
    domains: ["res.cloudinary.com"],
  },
  // Expose the backend URL to client-side code
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.BACKEND_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
