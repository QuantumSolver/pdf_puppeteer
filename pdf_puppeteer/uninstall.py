from .install import remove_pdf_generator_option

def before_uninstall():
    remove_pdf_generator_option()