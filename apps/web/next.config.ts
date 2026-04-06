import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  webpack(config) {
    // Redirect @atlas/shared imports to the compiled dist so webpack does not
    // try to process NodeNext TypeScript source with .js extension re-exports.
    config.resolve.alias = {
      ...config.resolve.alias,
      "@atlas/shared": path.resolve(__dirname, "../../packages/shared/dist/index.js"),
    };
    return config;
  },
};

export default nextConfig;
