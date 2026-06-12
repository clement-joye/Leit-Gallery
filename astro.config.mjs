import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://clement-joye.github.io",
  base: "/Leit-Gallery",
  vite: {
    plugins: [tailwindcss()],
  },
  output: "static",
});
