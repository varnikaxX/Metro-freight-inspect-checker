/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allows CI or a parallel dev server to use an isolated build directory.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.supabase.co" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
};

export default nextConfig;
