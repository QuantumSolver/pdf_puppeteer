import subprocess
import tempfile
import os
import json
import frappe
from frappe.utils.pdf import get_pdf as default_get_pdf

def map_frappe_options_to_puppeteer(options):
    """Convert Frappe PDF options to Puppeteer PDF options."""
    puppeteer_opts = {}
    # Page size
    page_size = options.get('page-size')
    if page_size:
        # Puppeteer expects format like 'A4', 'Letter', etc.
        puppeteer_opts['format'] = page_size
    # Orientation
    orientation = options.get('orientation')
    if orientation == 'Landscape':
        puppeteer_opts['landscape'] = True
    elif orientation == 'Portrait':
        puppeteer_opts['landscape'] = False
    # Margins
    margin_top = options.get('margin-top')
    margin_right = options.get('margin-right')
    margin_bottom = options.get('margin-bottom')
    margin_left = options.get('margin-left')
    if any([margin_top, margin_right, margin_bottom, margin_left]):
        margin = {}
        if margin_top:
            margin['top'] = margin_top
        if margin_right:
            margin['right'] = margin_right
        if margin_bottom:
            margin['bottom'] = margin_bottom
        if margin_left:
            margin['left'] = margin_left
        puppeteer_opts['margin'] = margin
    # Print background
    if options.get('print-background'):
        puppeteer_opts['printBackground'] = True
    # Page ranges
    page_ranges = options.get('page-ranges')
    if page_ranges:
        puppeteer_opts['pageRanges'] = page_ranges
    # Scale
    scale = options.get('scale')
    if scale:
        puppeteer_opts['scale'] = float(scale)
    return puppeteer_opts

def get_pdf(print_format, html, options, output, pdf_generator=None):
    """
    Generate PDF using Puppeteer Node script.
    This function is called by Frappe when pdf_generator is set to "puppeteer".
    """
    if pdf_generator != "puppeteer":
        # Fallback to default PDF generator
        return

    # Determine path to Node script
    app_path = frappe.get_app_path("pdf_puppeteer")
    script_path = os.path.join(app_path, "puppeteer_pdf.js")
    if not os.path.exists(script_path):
        # fallback to workspace root
        script_path = os.path.join(frappe.get_bench_path(), "puppeteer_pdf.js")
        if not os.path.exists(script_path):
            frappe.throw("Puppeteer script not found. Please ensure puppeteer_pdf.js is installed.")

    # Write HTML to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        html_path = f.name

    # Prepare options
    puppeteer_options = map_frappe_options_to_puppeteer(options)
    env = os.environ.copy()
    env['PDF_OPTIONS_JSON'] = json.dumps(puppeteer_options)

    try:
        # Prepare command: node script.js html_file - (output to stdout)
        cmd = ["node", script_path, html_path, "-"]
        # Use subprocess to run Node script and capture PDF stdout
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            timeout=30,
            check=True
        )
        pdf = result.stdout
        if not pdf:
            frappe.throw("Puppeteer failed to generate PDF: " + result.stderr.decode())
        # Write PDF to output file if output is a file path, else return bytes
        if isinstance(output, str):
            with open(output, 'wb') as f:
                f.write(pdf)
        else:
            # output is a file-like object (BytesIO)
            output.write(pdf)
    except subprocess.TimeoutExpired:
        frappe.throw("PDF generation timed out.")
    except subprocess.CalledProcessError as e:
        frappe.throw(f"Puppeteer error: {e.stderr.decode()}")
    finally:
        os.unlink(html_path)