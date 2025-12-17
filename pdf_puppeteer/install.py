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

            # Try different Chromium package names for different distributions
            chromium_packages = [
                ("chromium-browser", "Standard Chromium browser package"),
                ("chromium", "Alternative Chromium package name"),
                ("chromium-chromedriver", "Chromium with chromedriver"),
                ("google-chrome-stable", "Google Chrome stable version"),
                ("chrome-gnome-shell", "Chrome GNOME shell (fallback)"),
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

                        # Try different package names for this manager
                        for package_name, package_desc in chromium_packages:
                            try:
                                print(f"Attempting to install {package_name} ({package_desc})...")

                                # Special handling for apt-get (Debian/Ubuntu)
                                if manager == "apt-get":
                                    # Update package list first
                                    subprocess.run(
                                        ["sudo", manager, "update"],
                                        capture_output=True,
                                        text=True,
                                        check=True
                                    )

                                # Install the package
                                install_result = subprocess.run(
                                    [manager] + args[:-1] + [package_name],
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )

                                print(f"✅ Successfully installed {package_name} using {manager}")
                                return

                            except subprocess.CalledProcessError as e:
                                print(f"❌ Failed to install {package_name}: {e.stderr.strip()}")
                                continue
                            except Exception as e:
                                print(f"⚠️  Error installing {package_name}: {str(e)}")
                                continue

                except subprocess.CalledProcessError as e:
                    print(f"Failed to install Chromium using {manager}: {e.stderr}")
                    continue
                except Exception as e:
                    print(f"Error checking {manager}: {e}")
                    continue

            print("⚠️  Could not automatically install Chromium. Please install it manually.")
            print("\n📋 **Installation Options:**")
            print("• Ubuntu/Debian: sudo apt-get install chromium-browser")
            print("• CentOS/RHEL: sudo yum install chromium")
            print("• Alpine: sudo apk add chromium")
            print("• Google Chrome: sudo apt-get install google-chrome-stable")
            print("\n🐳 **For Docker Environments:**")
            print("1. Install Chromium in your Dockerfile:")
            print("   RUN apt-get update && apt-get install -y chromium-browser")
            print("2. Or use a pre-built image with Chromium")
            print("3. Or install Google Chrome instead:")
            print("   RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb")
            print("   RUN apt-get install -y ./google-chrome-stable_current_amd64.deb")
            print("\n💡 **Alternative:** You can also modify puppeteer_pdf.js to use an existing")
            print("   Chrome/Chromium binary path if one is already available in your system.")

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