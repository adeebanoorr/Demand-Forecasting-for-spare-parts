/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                teal: {
                    light: '#3dbbb1',
                    DEFAULT: '#26988A',
                    dark: '#1e7a6e',
                },
                accent: {
                    DEFAULT: '#CC8062',
                    light: '#e1a68d',
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
