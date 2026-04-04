/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terra:     '#EA785B',
        blush:     '#F7E9DE',
        pink:      '#F0BBB4',
        carnation: '#F15F61',
        peach:     '#FFBE98',
        espresso:  '#3D2B2B',
        rosewood:  '#7A4848',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        serif:   ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans:    ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}