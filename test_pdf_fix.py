"""Test script to verify PDF generation works with bundled paths."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import Config
from pdf_generator import generate_prefilled_form

def test_pdf_paths():
    """Test that PDF generator can find logo paths."""
    print("Testing PDF generator paths...")
    print(f"DEFAULT_LOGO_PATH: {Config.DEFAULT_LOGO_PATH}")
    print(f"  Exists: {Config.DEFAULT_LOGO_PATH.exists()}")
    print(f"QA_LOGO_PATH: {Config.QA_LOGO_PATH}")
    print(f"  Exists: {Config.QA_LOGO_PATH.exists()}")
    
    assert Config.DEFAULT_LOGO_PATH.exists(), f"University logo not found: {Config.DEFAULT_LOGO_PATH}"
    assert Config.QA_LOGO_PATH.exists(), f"QA logo not found: {Config.QA_LOGO_PATH}"
    
    print("✓ All logo paths exist")

def test_pdf_generation():
    """Test that PDF generation works."""
    print("\nTesting PDF generation...")
    
    # Create a mock survey object
    class MockSurvey:
        id = 1
        faculty = "Test Faculty"
        department = "Test Department"
        professor = "Test Professor"
        subject = "Test Subject"
        semester = "Spring"
        academic_year = "2024"
    
    survey = MockSurvey()
    output_path = Path("test_form.pdf")
    
    try:
        result = generate_prefilled_form(
            survey,
            output_path,
            persistence=None,
            logo_path=None  # Let it use default from Config
        )
        print(f"✓ PDF generated: {result}")
        
        # Check that the PDF was created
        assert output_path.exists(), "PDF file was not created"
        file_size = output_path.stat().st_size
        print(f"✓ PDF file size: {file_size:,} bytes")
        
        # Clean up
        output_path.unlink()
        print("✓ Test PDF cleaned up")
        
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_pdf_paths()
    test_pdf_generation()
    print("\n✅ All PDF tests passed!")
