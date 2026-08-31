/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./analytics_revenue_portal/templates/**/*.html",
    "./growth_seo_agent/templates/**/*.html",
    "./social_media_agent/templates/**/*.html",
    "./static/js/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
      animation: { 'float': 'float 3s ease-in-out infinite', 'pulse-slow': 'pulse 3s ease-in-out infinite' }
    },
  },
  plugins: [],
}
