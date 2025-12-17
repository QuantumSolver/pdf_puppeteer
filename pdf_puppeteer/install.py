import frappe
import subprocess
import sys
import os
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def after_install():
    """Run after the app is installed."""
    install_chromium_if_needed()
    add_pdf_generator_option()

def before_install():
    pass

def install_chromium_if_needed():
    """Check if Chromium is installed and install it if needed."""
    try:
        # Check if chromium-browser is available
        result = subprocess.run(
            ["which", "chromium-browser"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Chromium not found, try to install it
            print("Chromium browser not found. Attempting to install...")

            # Try different package managers
            package_managers = [
                ("apt-get", ["install", "-y", "chromium-browser"]),
                ("yum", ["install", "-y", "chromium"]),
                ("dnf", ["install", "-y", "chromium"]),
                ("apk", ["add", "chromium"]),
                ("zypper", ["install", "-y", "chromium"])
            ]

            for manager, args in package_managers:
                try:
                    # Check if package manager is available
                    check_result = subprocess.run(
                        ["which", manager],
                        capture_output=True,
                        text=True
                    )

                    if check_result.returncode == 0:
                        print(f"Using {manager} to install Chromium...")

                        # Install chromium
                        install_result = subprocess.run(
                            [manager] + args,
                            capture_output=True,
                            text=True,
                            check=True
                        )

                        print(f"Chromium installed successfully using {manager}")
                        return

                except subprocess.CalledProcessError as e:
                    print(f"Failed to install Chromium using {manager}: {e.stderr}")
                    continue
                except Exception as e:
                    print(f"Error checking {manager}: {e}")
                    continue

            print("⚠️  Could not automatically install Chromium. Please install it manually.")
            print("On Ubuntu/Debian: sudo apt-get install chromium-browser")
            print("On CentOS/RHEL: sudo yum install chromium")
            print("On Alpine: sudo apk add chromium")

        else:
            print("✓ Chromium browser is already installed")

    except Exception as e:
        print(f"⚠️  Error checking/installing Chromium: {e}")
        print("Please ensure Chromium is installed manually for PDF generation to work.")

def add_pdf_generator_option():
    """Add 'puppeteer' option to Print Format's pdf_generator field."""
    options = (frappe.get_meta("Print Format").get_field("pdf_generator").options or "").split("\n")
    if "puppeteer" in options:
        return
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
    print("Added 'puppeteer' option to Print Format pdf_generator.")

def remove_pdf_generator_option():
    """Remove 'puppeteer' option from Print Format's pdf_generator field."""
    options = (frappe.get_meta("Print Format").get_field("pdf_generator").options or "").split("\n")
    if "puppeteer" not in options:
        return
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
    print("Removed 'puppeteer' option from Print Format pdf_generator.")