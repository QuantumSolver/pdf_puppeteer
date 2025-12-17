"""
Direct override for Frappe type validation to handle 'puppeteer' as a valid pdf_generator value.

This module patches Frappe's type validation system to accept 'puppeteer' as a valid
value for the pdf_generator parameter, bypassing the strict Literal type checking.
"""

import frappe
from frappe.utils.typing_validations import transform_parameter_types
from typing import Optional, Literal, Union
import functools
import inspect

# Original function reference
_original_transform_parameter_types = transform_parameter_types

def is_pdf_generator_parameter(func, args, kwargs):
    """Check if the current call involves pdf_generator parameter."""
    if not args and not kwargs:
        return False

    # Check if this is a print format download call
    if kwargs.get('method') == 'frappe.utils.print_format.download_pdf':
        return True

    # Check if pdf_generator is in the parameters
    all_params = {}
    if args:
        try:
            # Try to get parameter names from function signature
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            for i, arg in enumerate(args):
                if i < len(param_names):
                    all_params[param_names[i]] = arg
        except Exception:
            pass

    all_params.update(kwargs or {})

    return 'pdf_generator' in all_params

def patched_transform_parameter_types(func, args, kwargs):
    """Patched version of transform_parameter_types that handles pdf_generator specially."""

    # Check if this call involves pdf_generator parameter
    if is_pdf_generator_parameter(func, args, kwargs):
        # Get the pdf_generator value
        pdf_generator_value = None

        # Try to find pdf_generator in kwargs first
        if kwargs and 'pdf_generator' in kwargs:
            pdf_generator_value = kwargs['pdf_generator']
        # Then check args if we can map them
        elif args:
            try:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                for i, arg in enumerate(args):
                    if i < len(param_names) and param_names[i] == 'pdf_generator':
                        pdf_generator_value = arg
                        break
            except Exception:
                pass

        # If pdf_generator is 'puppeteer', we need to handle it specially
        if pdf_generator_value == 'puppeteer':
            # Temporarily modify the type annotation to include 'puppeteer'
            # We'll use a monkey-patched version of the function with updated annotations

            # Get the original function
            original_func = func

            # Create a wrapper that bypasses type validation for pdf_generator
            @functools.wraps(original_func)
            def wrapped_func(*inner_args, **inner_kwargs):
                # For pdf_generator parameter, we'll allow 'puppeteer'
                if 'pdf_generator' in inner_kwargs and inner_kwargs['pdf_generator'] == 'puppeteer':
                    # Temporarily set it to a valid value for type checking
                    original_pdf_generator = inner_kwargs['pdf_generator']
                    inner_kwargs['pdf_generator'] = 'chrome'  # Use a valid value for type checking

                    try:
                        # Call the original transform_parameter_types
                        result = _original_transform_parameter_types(original_func, inner_args, inner_kwargs)
                        # Restore the original value in the result
                        if result and len(result) > 1 and isinstance(result[1], dict):
                            result[1]['pdf_generator'] = original_pdf_generator
                        return result
                    finally:
                        inner_kwargs['pdf_generator'] = original_pdf_generator
                else:
                    # Normal processing
                    return _original_transform_parameter_types(original_func, inner_args, inner_kwargs)

            return wrapped_func(func, args, kwargs)

    # Normal processing for non-pdf_generator calls
    return _original_transform_parameter_types(func, args, kwargs)

def apply_pdf_generator_validation_patch():
    """Apply the monkey patch to fix pdf_generator validation."""
    try:
        # Import inspect for parameter inspection
        global inspect
        import inspect

        # Replace the original function with our patched version
        frappe.utils.typing_validations.transform_parameter_types = patched_transform_parameter_types

        # Also patch it in the module directly
        import frappe.utils.typing_validations
        frappe.utils.typing_validations.transform_parameter_types = patched_transform_parameter_types

        print("✅ Applied PDF generator validation patch - 'puppeteer' is now allowed")
        return True
    except Exception as e:
        try:
            frappe.log_error(f"Failed to apply PDF generator validation patch: {str(e)}", "PDF Puppeteer Patch Error")
        except:
            print(f"⚠️  Failed to apply PDF generator validation patch: {str(e)}")
        return False

def remove_pdf_generator_validation_patch():
    """Remove the monkey patch and restore original behavior."""
    try:
        # Restore original function
        frappe.utils.typing_validations.transform_parameter_types = _original_transform_parameter_types

        # Also restore in the module
        import frappe.utils.typing_validations
        frappe.utils.typing_validations.transform_parameter_types = _original_transform_parameter_types

        print("✅ Removed PDF generator validation patch")
        return True
    except Exception as e:
        try:
            frappe.log_error(f"Failed to remove PDF generator validation patch: {str(e)}", "PDF Puppeteer Patch Error")
        except:
            print(f"⚠️  Failed to remove PDF generator validation patch: {str(e)}")
        return False

# Note: Patch is NOT applied automatically on import to avoid frappe initialization issues
# It should be applied explicitly when frappe is ready (e.g., during installation)
# apply_pdf_generator_validation_patch()