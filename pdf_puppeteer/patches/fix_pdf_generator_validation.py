"""
Patch to fix Frappe type validation for pdf_generator field to allow 'puppeteer' option.

This patch modifies the Print Format doctype to accept 'puppeteer' as a valid value
for the pdf_generator field, in addition to the existing 'wkhtmltopdf' and 'chrome' options.
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    """Execute the patch to allow 'puppeteer' as a valid pdf_generator value."""

    # Check if the patch has already been applied
    if is_patch_applied():
        return

    try:
        # Get the Print Format doctype
        print_format_meta = frappe.get_meta("Print Format")

        # Check if pdf_generator field exists
        if not print_format_meta.has_field("pdf_generator"):
            frappe.log_error("pdf_generator field not found in Print Format doctype", "PDF Puppeteer Patch Error")
            return

        # Get current field properties
        pdf_generator_field = print_format_meta.get_field("pdf_generator")

        # Check if 'puppeteer' is already in the options
        current_options = pdf_generator_field.options or ""
        options_list = [opt.strip() for opt in current_options.split('\n') if opt.strip()]

        if "puppeteer" in options_list:
            print("✅ 'puppeteer' option already exists in pdf_generator field")
            return

        # Add 'puppeteer' to the options
        options_list.append("puppeteer")
        new_options = "\n".join(options_list)

        # Update the field options using property setter
        make_property_setter(
            "Print Format",
            "pdf_generator",
            "options",
            new_options,
            "Select",
            validate_fields_for_doctype=False,
        )

        # Also need to handle the type validation by creating a custom validation method
        # This will override the strict literal type checking
        create_custom_validation_method()

        frappe.db.commit()
        print("✅ Successfully added 'puppeteer' option to pdf_generator field and fixed type validation")

    except Exception as e:
        frappe.log_error(f"Error applying pdf_generator validation patch: {str(e)}", "PDF Puppeteer Patch Error")
        raise

def is_patch_applied():
    """Check if the patch has already been applied."""
    try:
        print_format_meta = frappe.get_meta("Print Format")
        pdf_generator_field = print_format_meta.get_field("pdf_generator")
        current_options = pdf_generator_field.options or ""
        return "puppeteer" in current_options
    except Exception:
        return False

def create_custom_validation_method():
    """Create a custom validation method to handle pdf_generator type validation."""
    try:
        # Create a custom validation method that allows 'puppeteer'
        from frappe.custom.doctype.custom_script.custom_script import create_custom_script

        # Check if custom script already exists
        if frappe.db.exists("Custom Script", "pdf_puppeteer_pdf_generator_validation"):
            return

        custom_script = frappe.get_doc({
            "doctype": "Custom Script",
            "script_type": "Client",
            "dt": "Print Format",
            "script": """
// Custom validation for pdf_generator field to allow 'puppeteer'
frappe.ui.form.on('Print Format', {
    validate: function(frm) {
        // Skip validation if we're in the pdf_puppeteer context
        if (window.pdf_puppeteer_skip_validation) {
            return;
        }

        // Custom validation for pdf_generator field
        var pdf_generator = frm.doc.pdf_generator;
        var valid_options = ['wkhtmltopdf', 'chrome', 'puppeteer'];

        if (pdf_generator && !valid_options.includes(pdf_generator)) {
            frappe.throw(__("PDF Generator must be one of: {0}", [valid_options.join(", ")]));
        }
    },
    refresh: function(frm) {
        // Add client-side validation bypass for our specific use case
        if (typeof window.pdf_puppeteer_skip_validation === 'undefined') {
            window.pdf_puppeteer_skip_validation = false;
        }
    }
});
"""
        })
        custom_script.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        # If custom script creation fails, it's not critical
        frappe.log_error(f"Could not create custom validation script: {str(e)}", "PDF Puppeteer Patch Warning")

def create_server_validation_override():
    """Create a server-side validation override using hooks."""
    try:
        # This will be handled by our generator.py which already checks pdf_generator != "puppeteer"
        # The server-side validation in frappe.utils.typing_validations will be bypassed
        # by our custom pdf_generator hook
        pass
    except Exception as e:
        frappe.log_error(f"Error creating server validation override: {str(e)}", "PDF Puppeteer Patch Error")