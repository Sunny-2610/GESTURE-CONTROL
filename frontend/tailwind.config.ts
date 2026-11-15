import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    borderRadius: { none: "0", sm: "2px" },
    boxShadow: { none: "none" },
    extend: {
      colors: {
        paper: { DEFAULT: "#ECE9E2", 2: "#E1DDD3" },
        ink: { DEFAULT: "#1A1916", muted: "#66625A" },
        signal: { DEFAULT: "#FF4A1C", deep: "#E63E0E", text: "#BF3508" },
      },
      fontFamily: {
        sans: ["Schibsted Grotesk", "system-ui", "sans-serif"],
        mono: ["DM Mono", "ui-monospace", "Menlo", "Consolas", "monospace"],
      },
      fontSize: {
        display: ["96px", { lineHeight: "88px", fontWeight: "500" }],
        title: ["72px", { lineHeight: "72px", fontWeight: "600" }],
        heading: ["20px", { lineHeight: "28px", fontWeight: "600" }],
        body: ["15px", { lineHeight: "24px" }],
        data: ["13px", { lineHeight: "20px", fontWeight: "400" }],
        label: ["11px", { lineHeight: "16px", letterSpacing: "0.06em", fontWeight: "500" }],
        numeral: ["32px", { lineHeight: "32px", fontWeight: "500" }],
      },
      spacing: { topbar: "56px", status: "28px", alert: "36px" },
    },
  },
} satisfies Config;
