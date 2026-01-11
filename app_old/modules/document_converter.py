"""
Document Conversion Module

This module provides functionality to convert between different document formats.
"""
import os
import logging
import subprocess
import sys
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import tempfile
import shutil

# Check if pdftotree is available
try:
    import pdftotree
    PDFTOTREE_AVAILABLE = True
except ImportError:
    from .pdftotree_mock import parse as pdftotree_parse, PDFToTreeParseError
    PDFTOTREE_AVAILABLE = False
    print("Warning: Using mock pdftotree implementation")

logger = logging.getLogger(__name__)

class DocumentConverter:
    """
    A class to handle document conversions between various formats.
    
    Supported conversions:
    - PDF to Word (.docx)
    - PDF to images (.jpg, .png)
    - Word to PDF
    - PDF to LaTeX
    - LaTeX to PDF
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the document converter.
        
        Args:
            temp_dir: Directory to store temporary files (default: system temp)
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix='doc_converter_')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def __del__(self):
        """Clean up temporary files when the object is destroyed."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temp directory: {e}")
    
    def convert(self, 
               input_path: str, 
               output_path: str, 
               output_format: str,
               **kwargs) -> Tuple[bool, str]:
        """
        Convert a document to the specified format.
        
        Args:
            input_path: Path to the input file
            output_path: Path where the converted file should be saved
            output_format: Target format (e.g., 'docx', 'jpg', 'pdf', 'tex')
            **kwargs: Additional format-specific options
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            input_path = os.path.abspath(input_path)
            output_path = os.path.abspath(output_path)
            
            if not os.path.exists(input_path):
                return False, f"Input file not found: {input_path}"
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Determine conversion type
            input_ext = os.path.splitext(input_path)[1].lower()
            output_ext = os.path.splitext(output_path)[1].lower()
            
            # Perform the conversion based on file types
            if input_ext == '.pdf' and output_ext == '.docx':
                return self._pdf_to_docx(input_path, output_path, **kwargs)
            elif input_ext == '.pdf' and output_ext in ('.jpg', '.jpeg', '.png'):
                return self._pdf_to_image(input_path, output_path, **kwargs)
            elif input_ext in ('.doc', '.docx') and output_ext == '.pdf':
                return self._docx_to_pdf(input_path, output_path, **kwargs)
            elif input_ext == '.pdf' and output_ext == '.tex':
                return self._pdf_to_latex(input_path, output_path, **kwargs)
            elif input_ext == '.tex' and output_ext == '.pdf':
                return self._latex_to_pdf(input_path, output_path, **kwargs)
            else:
                return False, f"Unsupported conversion: {input_ext} to {output_ext}"
                
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}", exc_info=True)
            return False, f"Conversion error: {str(e)}"
    
    def _pdf_to_docx(self, input_path: str, output_path: str, **kwargs) -> Tuple[bool, str]:
        """Convert PDF to Word document using pdf2docx."""
        try:
            from pdf2docx import Converter
            
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            return True, f"Successfully converted to DOCX: {output_path}"
            
        except ImportError:
            logger.error("pdf2docx library not installed. Install with: pip install pdf2docx")
            return False, "PDF to DOCX conversion requires pdf2docx library"
        except Exception as e:
            return False, f"PDF to DOCX conversion failed: {str(e)}"
    
    def _pdf_to_image(self, input_path: str, output_path: str, **kwargs) -> Tuple[bool, str]:
        """Convert PDF to image(s) using pdf2image."""
        try:
            from pdf2image import convert_from_path
            
            # Get page number (default to first page)
            page_number = kwargs.get('page', 1) - 1  # 0-based index
            
            # Convert the PDF to images
            images = convert_from_path(input_path, first_page=page_number+1, last_page=page_number+1)
            
            if not images:
                return False, "No pages found in PDF"
            
            # Save the first (or specified) page
            images[0].save(output_path, 'JPEG' if output_path.lower().endswith(('.jpg', '.jpeg')) else 'PNG')
            
            return True, f"Successfully converted to image: {output_path}"
            
        except ImportError:
            logger.error("pdf2image library not installed. Install with: pip install pdf2image")
            return False, "PDF to image conversion requires pdf2image library"
        except Exception as e:
            return False, f"PDF to image conversion failed: {str(e)}"
    
    def _docx_to_pdf(self, input_path: str, output_path: str, **kwargs) -> Tuple[bool, str]:
        """Convert Word document to PDF using docx2pdf."""
        try:
            from docx2pdf import convert
            
            convert(input_path, output_path)
            return True, f"Successfully converted to PDF: {output_path}"
            
        except ImportError:
            logger.error("docx2pdf library not installed. Install with: pip install docx2pdf")
            return False, "DOCX to PDF conversion requires docx2pdf library"
        except Exception as e:
            return False, f"DOCX to PDF conversion failed: {str(e)}"
    
    def _pdf_to_latex(self, input_path: str, output_path: str, **kwargs) -> Tuple[bool, str]:
        """
        Convert PDF to LaTeX using pdftotree or mock implementation.
        
        Args:
            input_path: Path to the input PDF file
            output_path: Path where the output LaTeX file should be saved
            **kwargs: Additional arguments passed to pdftotree.parse()
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not PDFTOTREE_AVAILABLE:
                # Use mock implementation
                output_dir = os.path.dirname(output_path) or '.'
                pdftotree_parse(input_path, output_dir=output_dir)
                return True, f"Successfully converted to LaTeX using mock implementation: {output_path}"
            
            # Use real pdftotree if available
            pdftotree.parse(
                input_path, 
                html_path=None, 
                model_type=kwargs.get('model_type'), 
                model_path=kwargs.get('model_path'),
                output_tex_path=output_path, 
                visualize=kwargs.get('visualize', False)
            )
            
            return True, f"Successfully converted to LaTeX: {output_path}"
            
        except PDFToTreeParseError as e:
            error_msg = f"PDF to LaTeX conversion failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"PDF to LaTeX conversion failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _latex_to_pdf(self, input_path: str, output_path: str, **kwargs) -> Tuple[bool, str]:
        """Compile LaTeX to PDF using pdflatex."""
        try:
            # Create a temporary directory for the LaTeX build
            temp_dir = tempfile.mkdtemp(dir=self.temp_dir)
            
            # Copy the input file to the temp directory
            input_file = os.path.join(temp_dir, os.path.basename(input_path))
            shutil.copy2(input_path, temp_dir)
            
            # Run pdflatex to compile the document
            cmd = ['pdflatex', '-interaction=nonstopmode', f'-output-directory={temp_dir}', input_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = f"LaTeX compilation failed: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
            
            # Find the generated PDF (same name as input but with .pdf extension)
            pdf_file = os.path.splitext(input_file)[0] + '.pdf'
            if not os.path.exists(pdf_file):
                return False, f"PDF output not found: {pdf_file}"
            
            # Move the output file to the desired location
            shutil.move(pdf_file, output_path)
            
            # Clean up auxiliary files
            for ext in ['.aux', '.log', '.out']:
                aux_file = os.path.splitext(input_file)[0] + ext
                if os.path.exists(aux_file):
                    os.remove(aux_file)
            
            return True, f"Successfully compiled to PDF: {output_path}"
            
        except Exception as e:
            return False, f"LaTeX to PDF compilation failed: {str(e)}"

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python document_converter.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    converter = DocumentConverter()
    success, message = converter.convert(input_file, output_file, 
                                       os.path.splitext(output_file)[1][1:])  # Get format from extension
    
    if success:
        print(f"Conversion successful: {message}")
    else:
        print(f"Conversion failed: {message}")
