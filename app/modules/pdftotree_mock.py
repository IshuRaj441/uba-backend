"""
Mock pdftotree module to avoid dependency issues.
Replace with actual pdftotree implementation when available.
"""
import os
import shutil
from typing import Optional

class PDFToTreeParseError(Exception):
    pass

def parse(pdf_file: str, 
          output_dir: Optional[str] = None, 
          model_type: str = "paddle",
          model_convert: str = "paddle",
          visual_metrics: bool = False,
          include_page_bbox: bool = False,
          **kwargs):
    """
    Mock implementation of pdftotree.parse()
    """
    print(f"Mock pdftotree.parse() called with file: {pdf_file}")
    
    # If output_dir is not provided, create a default one
    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        output_dir = os.path.join(os.path.dirname(pdf_file), f"{base_name}_output")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a simple HTML file as mock output
    output_file = os.path.join(output_dir, "output.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"""<html>
<head><title>Mock PDF to HTML Conversion</title></head>
<body>
<h1>Mock PDF to HTML Conversion</h1>
<p>This is a mock implementation of pdftotree.parse()</p>
<p>Original PDF: {os.path.basename(pdf_file)}</p>
<p>To use the real pdftotree, please install it manually.</p>
</body>
</html>""")
    
    return output_file

# For backward compatibility
parse_pdf = parse
