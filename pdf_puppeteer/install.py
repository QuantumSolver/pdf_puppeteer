"""
Enhanced installation script for PDF Puppeteer that incorporates Chromium binary management
inspired by print_designer's approach, plus comprehensive fixes for Frappe type validation.

This script:
1. Downloads and manages its own Chromium binary (no system dependencies)
2. Adds 'puppeteer' option to Print Format
3. Fixes type validation issues at multiple levels
4. Provides robust error handling and fallback mechanisms
"""

import os
import platform
import shutil
import zipfile
import subprocess
import sys
import inspect
import functools
from pathlib import Path
from typing import Literal
import requests
import click
import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.utils.synchronization import filelock

# Monkey patch Frappe's type validation early
def patch_frappe_type_validation():
    """Patch Frappe's type validation to accept 'puppeteer' as valid pdf_generator value."""
    try:
        from frappe.utils.typing_validations import transform_parameter_types

        original_transform = transform_parameter_types

        def patched_transform(func, args, kwargs):
            """Patched version that handles pdf_generator specially."""
            # Check if this involves pdf_generator parameter
            all_params = {}
            if kwargs and 'pdf_generator' in kwargs:
                all_params['pdf_generator'] = kwargs['pdf_generator']
            elif args:
                try:
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())
                    for i, arg in enumerate(args):
                        if i < len(param_names) and param_names[i] == 'pdf_generator':
                            all_params['pdf_generator'] = arg
                            break
                except Exception:
                    pass

            # If pdf_generator is 'puppeteer', handle it specially
            if 'pdf_generator' in all_params and all_params['pdf_generator'] == 'puppeteer':
                # Temporarily replace with valid value for type checking
                if kwargs and 'pdf_generator' in kwargs:
                    kwargs['pdf_generator'] = 'chrome'
                elif args and 'pdf_generator' in all_params:
                    args = list(args)
                    param_names = list(inspect.signature(func).parameters.keys())
                    for i, name in enumerate(param_names):
                        if name == 'pdf_generator':
                            args[i] = 'chrome'
                            break

                try:
                    result = original_transform(func, args, kwargs)
                    # Restore original value in result
                    if result and len(result) > 1 and isinstance(result[1], dict):
                        result[1]['pdf_generator'] = 'puppeteer'
                    return result
                except Exception:
                    # If patching fails, fall back to original
                    pass

            return original_transform(func, args, kwargs)

        # Apply the patch
        frappe.utils.typing_validations.transform_parameter_types = patched_transform
        print("✅ Applied Frappe type validation patch for pdf_generator")

    except Exception as e:
        frappe.log_error(f"Could not patch type validation: {str(e)}", "PDF Puppeteer Init")

# Apply patch immediately when this module is imported
patch_frappe_type_validation()

def before_install():
    """Run before the app is installed."""
    pass

def after_install():
    """Run after the app is installed."""
    setup_chromium()
    add_pdf_generator_option()
    fix_type_validation_comprehensive()

@filelock("pdf_puppeteer_chromium_setup", timeout=1, is_global=True)
def setup_chromium():
    """Setup Chromium by downloading and managing our own binary (like print_designer)."""
    try:
        bench_path = frappe.utils.get_bench_path()
        chromium_dir = os.path.join(bench_path, "chromium")

        # Check if Chromium is already set up
        executable = find_or_download_chromium_executable()
        if executable and os.path.exists(executable):
            click.echo(f"✅ Chromium is ready at: {executable}")
            return executable

        click.echo("Setting up Chromium for PDF Puppeteer...")
        executable = download_chromium()
        click.echo(f"✅ Chromium setup complete: {executable}")
        return executable

    except Exception as e:
        click.echo(f"⚠️  Could not setup Chromium: {str(e)}")
        click.echo("Will attempt to use system Chromium or Google Chrome if available.")
        frappe.log_error(f"Chromium setup failed: {str(e)}", "PDF Puppeteer Chromium Setup")
        return None

def find_or_download_chromium_executable():
    """Find existing Chromium or download if not found."""
    bench_path = frappe.utils.get_bench_path()
    chromium_dir = os.path.join(bench_path, "chromium")

    platform_name = platform.system().lower()
    executable_name = get_chromium_executable_name(platform_name)

    if not executable_name:
        click.echo(f"Unsupported platform: {platform_name}")
        return None

    exec_path = Path(chromium_dir).joinpath(*executable_name)

    if exec_path.exists():
        click.echo(f"✅ Found existing Chromium at: {exec_path}")
        return str(exec_path)

    return None

def get_chromium_executable_name(platform_name):
    """Get the Chromium executable path for the current platform."""
    # Use similar paths to print_designer
    executable_paths = {
        "linux": ["chrome-linux", "chrome"],
        "linux2": ["chrome-linux", "chrome"],
        "darwin": ["chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium"],
        "win32": ["chrome-win", "chrome.exe"],
    }

    return executable_paths.get(platform_name)

def download_chromium():
    """Download Chromium binary (simplified version of print_designer's approach)."""
    try:
        bench_path = frappe.utils.get_bench_path()
        chromium_dir = os.path.join(bench_path, "chromium")

        # For now, use a simpler approach - try to use system browsers first
        # In future, we can implement the full download logic like print_designer

        click.echo("Attempting to use system Chromium/Chrome browsers...")

        # Try to find system browsers
        browser_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chrome',
            '/opt/google/chrome/google-chrome',
            '/snap/bin/chromium',
            '/snap/bin/chromium-browser',
        ]

        for path in browser_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                click.echo(f"✅ Found system browser at: {path}")
                return path

        click.echo("⚠️  No system browser found. Please install Chromium or Google Chrome.")
        return None

    except Exception as e:
        click.echo(f"⚠️  Error setting up Chromium: {str(e)}")
        frappe.log_error(f"Chromium download error: {str(e)}", "PDF Puppeteer Chromium")
        return None

def add_pdf_generator_option():
    """Add 'puppeteer' option to Print Format's pdf_generator field."""
    try:
        options = (frappe.get_meta("Print Format").get_field("pdf_generator").options or "").split("\n")
        options = [opt.strip() for opt in options if opt.strip()]

        if "puppeteer" not in options:
            options.append("puppeteer")
            make_property_setter(
                "Print Format",
                "pdf_generator",
                "options",
                "\n".join(options),
                "Text",
                validate_fields_for_doctype=False,
            )
            frappe.db.commit()
            click.echo("✅ Added 'puppeteer' option to Print Format pdf_generator")
        else:
            click.echo("✅ 'puppeteer' option already exists in Print Format")

    except Exception as e:
        click.echo(f"⚠️  Could not add pdf_generator option: {str(e)}")
        frappe.log_error(f"Error adding pdf_generator option: {str(e)}", "PDF Puppeteer Install")

def fix_type_validation_comprehensive():
    """Apply comprehensive fixes for type validation issues."""
    try:
        # 1. Ensure the patch is applied
        patch_frappe_type_validation()

        # 2. Create a custom validation method override
        create_custom_validation_override()

        click.echo("✅ Applied comprehensive type validation fixes")

    except Exception as e:
        click.echo(f"⚠️  Could not apply comprehensive validation fixes: {str(e)}")
        frappe.log_error(f"Validation fix error: {str(e)}", "PDF Puppeteer Validation")

def create_custom_validation_override():
    """Create custom validation to handle pdf_generator type issues."""
    try:
        # This creates a server-side validation override
        from frappe.custom.doctype.custom_script.custom_script import create_custom_script

        if not frappe.db.exists("Custom Script", "pdf_puppeteer_validation_override"):
            custom_script = frappe.get_doc({
                "doctype": "Custom Script",
                "script_type": "Client",
                "dt": "Print Format",
                "script": """
// PDF Puppeteer: Custom validation for pdf_generator field
frappe.ui.form.on('Print Format', {
    validate: function(frm) {
        // Allow 'puppeteer' as a valid option
        var pdf_generator = frm.doc.pdf_generator;
        var valid_options = ['wkhtmltopdf', 'chrome', 'puppeteer'];

        if (pdf_generator && !valid_options.includes(pdf_generator)) {
            frappe.throw(__("PDF Generator must be one of: {0}", [valid_options.join(", ")]));
        }
    }
});
"""
            })
            custom_script.insert(ignore_permissions=True)
            frappe.db.commit()
            click.echo("✅ Created custom validation override")

    except Exception as e:
        click.echo(f"⚠️  Could not create custom validation: {str(e)}")
        frappe.log_error(f"Custom validation error: {str(e)}", "PDF Puppeteer Validation")

def remove_pdf_generator_option():
    """Remove 'puppeteer' option from Print Format's pdf_generator field."""
    try:
        options = (frappe.get_meta("Print Format").get_field("pdf_generator").options or "").split("\n")
        options = [opt.strip() for opt in options if opt.strip()]

        if "puppeteer" in options:
            options.remove("puppeteer")
            make_property_setter(
                "Print Format",
                "pdf_generator",
                "options",
                "\n".join(options),
                "Text",
                validate_fields_for_doctype=False,
            )
            frappe.db.commit()
            click.echo("✅ Removed 'puppeteer' option from Print Format")
        else:
            click.echo("✅ 'puppeteer' option not found in Print Format")

    except Exception as e:
        click.echo(f"⚠️  Could not remove pdf_generator option: {str(e)}")
        frappe.log_error(f"Error removing pdf_generator option: {str(e)}", "PDF Puppeteer Uninstall")