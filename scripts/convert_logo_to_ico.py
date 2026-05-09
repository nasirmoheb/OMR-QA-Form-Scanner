"""Convert PNG logo to ICO format for Windows executable.

This script converts the app logo from PNG to ICO format with multiple sizes
for optimal display at different resolutions in Windows.

Usage:
    python convert_logo_to_ico.py

Input:  assets/app logo.png
Output: assets/app_icon.ico
"""

from PIL import Image
from pathlib import Path


def convert_logo_to_ico():
    """Convert the PNG logo to ICO format with multiple sizes."""
    # Paths
    logo_path = Path("assets/app logo.png")
    ico_path = Path("assets/app_icon.ico")
    
    if not logo_path.exists():
        print(f"❌ Error: Logo file not found: {logo_path}")
        return False
    
    try:
        # Load the PNG logo
        img = Image.open(logo_path)
        
        # ICO files work best with square images at standard sizes
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        
        # Convert to RGBA if not already
        img = img.convert('RGBA')
        
        # Create a square canvas (use the larger dimension)
        width, height = img.size
        max_dim = max(width, height)
        
        # Create a new square image with transparent background
        square_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
        
        # Paste the original image centered
        offset = ((max_dim - width) // 2, (max_dim - height) // 2)
        square_img.paste(img, offset, img if img.mode == 'RGBA' else None)
        
        # Save as ICO with multiple sizes
        square_img.save(ico_path, format='ICO', sizes=sizes)
        
        print(f"✓ Icon created successfully: {ico_path}")
        print(f"  Original size: {width}x{height}")
        print(f"  Icon sizes: {', '.join(f'{s[0]}x{s[1]}' for s in sizes)}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting logo: {e}")
        return False


if __name__ == "__main__":
    convert_logo_to_ico()
