# PDF Puppeteer Frappe App

This Frappe app adds a new PDF generator option "puppeteer" to Print Format, using Puppeteer (headless Chrome) to generate PDFs from HTML.

## Features

- Adds "puppeteer" option to Print Format's PDF generator dropdown.
- Uses Node.js script `puppeteer_pdf.js` to generate PDF via Puppeteer.
- Supports page size, margins, orientation, and other PDF options.
- Lightweight integration: no separate HTTP server required.

## Installation

### Prerequisites

- Frappe Bench with Node.js installed.
- Chromium browser installed on the system (e.g., `chromium-browser` on Ubuntu).

### Steps

1. Install the app in your bench:

   ```bash
   bench get-app pdf_puppeteer
   bench install-app pdf_puppeteer
   ```

   Or if you are developing locally, clone this repository into your `apps` directory and install.

2. The app will automatically attempt to install Chromium browser if it's not already installed. If automatic installation fails, you may need to install it manually (see below).

2. Install Node dependencies:

   ```bash
   npm install puppeteer
   ```

   The app expects `puppeteer_pdf.js` to be in the bench root (or accessible via path). The installation script will copy it.

3. Ensure Chromium is installed:

   ```bash
   sudo apt-get install chromium-browser   # Ubuntu/Debian
   ```

4. After installation, the "puppeteer" option will appear in Print Format's PDF generator field.

## Usage

1. Create or edit a Print Format.
2. Set "PDF Generator" to "puppeteer".
3. When printing/downloading PDF, the app will call the Puppeteer script to generate the PDF.

## Configuration

You can adjust Puppeteer launch arguments and PDF options by modifying `pdf_puppeteer/generator.py` and `puppeteer_pdf.js`.

### Environment Variables

- `PDF_OPTIONS_JSON`: JSON string of PDF options (passed from Frappe).

### Customizing Chromium Path

If Chromium is installed in a different location, update `executablePath` in `puppeteer_pdf.js`.

## Development

- The main PDF generation hook is in `pdf_puppeteer/generator.py`.
- The Node script is `puppeteer_pdf.js` (located in bench root).
- To test locally, run:

   ```bash
   node puppeteer_pdf.js test.html output.pdf
   ```

## Troubleshooting

### Puppeteer fails to launch browser

- The app automatically attempts to install Chromium during installation.
- If automatic installation fails, you may need to install Chromium manually:
  - Ubuntu/Debian: `sudo apt-get install chromium-browser`
  - CentOS/RHEL: `sudo yum install chromium`
  - Alpine: `sudo apk add chromium`
- Check that the user running the bench has permission to launch Chromium.
- If running in a Docker container, you may need to install additional dependencies.

### PDF generation timeout

- Increase timeout in `generator.py` (default 30 seconds).

### Missing options

- The mapping between Frappe PDF options and Puppeteer options is defined in `map_frappe_options_to_puppeteer`. Extend as needed.

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/pdf_puppeteer
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

## License

MIT
