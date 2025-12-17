__version__ = "1.0.0"

# Import overrides to patch Frappe type validation early
try:
    from .overrides import pdf_generator_validation
    pdf_generator_validation.apply_pdf_generator_validation_patch()
except Exception as e:
    # If import fails, log the error but don't crash
    import frappe
    frappe.log_error(f"PDF Puppeteer: Could not apply validation patch: {str(e)}", "PDF Puppeteer Init Error")
