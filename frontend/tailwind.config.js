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
                    DEFAULT: '#0075BE',
                    dark: '#1e7a6e',
                },
                accent: {
                    DEFAULT: '#234FA2',
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
