const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

/**
 * Generate PDF from HTML string.
 * @param {string} html - HTML content
 * @param {object} options - PDF options (format, margin, landscape, etc.)
 * @returns {Promise<Buffer>} PDF buffer
 */
async function generatePdfFromHtml(html, options = {}) {
    // Try to find available browser executables
    const browserPaths = [
        '/usr/bin/chromium-browser',  // Standard Chromium on Ubuntu/Debian
        '/usr/bin/chromium',          // Alternative Chromium path
        '/usr/bin/google-chrome',     // Google Chrome stable
        '/usr/bin/google-chrome-stable', // Google Chrome stable (alternative)
        '/usr/bin/chrome',            // Generic chrome
        '/usr/bin/chromium-browser-sandbox', // Chromium with sandbox
        '/opt/google/chrome/google-chrome', // Google Chrome in /opt
        '/snap/bin/chromium',         // Snap package
        '/snap/bin/chromium-browser', // Snap package (alternative)
    ];

    // Find the first available browser
    let executablePath = null;
    for (const path of browserPaths) {
        try {
            // Check if the browser exists and is executable
            require('fs').accessSync(path, require('fs').constants.X_OK);
            executablePath = path;
            console.log(`🔍 Using browser at: ${path}`);
            break;
        } catch (e) {
            // Browser not found at this path, try next one
        }
    }

    if (!executablePath) {
        throw new Error('No supported browser found. Please install Chromium or Google Chrome. ' +
                       'Supported browsers: chromium-browser, chromium, google-chrome, google-chrome-stable');
    }

    const browser = await puppeteer.launch({
        headless: 'new',
        executablePath: executablePath,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
        ],
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });

        // Write HTML to a temporary file to load as file:// URL
        // This ensures relative resources (images, CSS) are resolved if they are relative to the temp directory.
        // However, we'll use setContent for simplicity; if resources are absolute URLs they will work.
        await page.setContent(html, { waitUntil: 'networkidle0', timeout: 30000 });

        const pdfOptions = {
            format: options.format || 'A4',
            printBackground: options.printBackground !== false,
            margin: options.margin || { top: '1cm', right: '1cm', bottom: '1cm', left: '1cm' },
            landscape: options.landscape || false,
            ...options,
        };

        const pdfBuffer = await page.pdf(pdfOptions);
        return pdfBuffer;
    } finally {
        await browser.close();
    }
}

/**
 * CLI usage: node puppeteer_pdf.js <input_html_file> <output_pdf_file> [options_json_file]
 * or read HTML from stdin and output PDF to stdout with options from environment PDF_OPTIONS_JSON.
 */
async function main() {
    const args = process.argv.slice(2);
    let options = {};
    // Read options from environment variable PDF_OPTIONS_JSON (JSON string)
    if (process.env.PDF_OPTIONS_JSON) {
        try {
            options = JSON.parse(process.env.PDF_OPTIONS_JSON);
        } catch (e) {
            console.error('Failed to parse PDF_OPTIONS_JSON:', e.message);
        }
    }
    // If third argument is provided, treat as options JSON file
    if (args.length >= 3) {
        try {
            const optionsJson = await fs.readFile(args[2], 'utf8');
            options = { ...options, ...JSON.parse(optionsJson) };
        } catch (e) {
            console.error('Failed to read options file:', e.message);
        }
    }

    if (args.length === 0) {
        // Read HTML from stdin
        const html = await new Promise((resolve) => {
            let data = '';
            process.stdin.on('data', chunk => data += chunk);
            process.stdin.on('end', () => resolve(data));
        });
        const pdf = await generatePdfFromHtml(html, options);
        process.stdout.write(pdf);
    } else if (args.length >= 2) {
        // Input file and output file
        const inputFile = args[0];
        const outputFile = args[1];
        const html = await fs.readFile(inputFile, 'utf8');
        const pdf = await generatePdfFromHtml(html, options);
        await fs.writeFile(outputFile, pdf);
        console.log(`PDF written to ${outputFile}`);
    } else {
        console.error('Usage: node puppeteer_pdf.js [input.html output.pdf [options.json]]');
        console.error('If no arguments, reads HTML from stdin and writes PDF to stdout.');
        console.error('Options can be provided via environment variable PDF_OPTIONS_JSON (JSON string) or via options.json file.');
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(err => {
        console.error(err);
        process.exit(1);
    });
}

module.exports = { generatePdfFromHtml };