/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './**/templates/**/*.html',
        './stugov/static/js/**/*.js',
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Geist', 'ui-sans-serif', 'system-ui', 'sans-serif'],
            },
            colors: {
                'rpi-red': '#d6001c',
                'rpi-red-dark': '#a50015',
                'stugov-dark': '#1a1a2e',
                'stugov-gray': '#4a4a68',
            },
            typography: ({ theme }) => ({
                DEFAULT: {
                    css: {
                        'a': {
                            color: '#d6001c',
                            textDecoration: 'underline',
                            textUnderlineOffset: '2px',
                            transition: 'color 150ms ease',
                        },
                        'a:hover': {
                            color: '#a50015',
                        },
                        'hr': {
                            marginTop: '1rem',
                            marginBottom: '1rem',
                            borderColor: '#e5e7eb',
                        },
                        'p': {
                            marginTop: '0',
                            marginBottom: '1.0rem',
                            lineHeight: '1.4em',
                        },
                        'blockquote': {
                            borderLeftColor: '#d6001c',
                        },
                    },
                },
            }),
        }
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
