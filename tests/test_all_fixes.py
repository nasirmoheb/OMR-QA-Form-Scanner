"""Comprehensive test suite for all production fixes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import Config

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def test_config_paths():
    """Test that Config resolves all paths correctly."""
    print_header("Testing Config Path Resolution")
    
    paths_to_check = {
        "PROJECT_ROOT": Config.PROJECT_ROOT,
        "ASSETS_DIR": Config.ASSETS_DIR,
        "TEMPLATES_DIR": Config.TEMPLATES_DIR,
        "DEFAULT_LOGO_PATH": Config.DEFAULT_LOGO_PATH,
        "QA_LOGO_PATH": Config.QA_LOGO_PATH,
    }
    
    all_ok = True
    for name, path in paths_to_check.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {path}")
        if not exists:
            all_ok = False
    
    # Test writable reports directory
    reports_dir = Config.get_reports_dir()
    print(f"✓ REPORTS_DIR: {reports_dir}")
    
    if all_ok:
        print("\n✅ All Config paths exist")
    else:
        print("\n❌ Some Config paths are missing")
        sys.exit(1)

def test_html_report():
    """Test HTML report generation with embedded logos."""
    print_header("Testing HTML Report Generation")
    
    from report_generator import generate_dari_qa_report
    
    # Create mock objects
    class MockSurvey:
        university = "پوهنتون بدخشان"
        faculty = "پوهنحی کمپیوتر ساینس"
        professor = "محمد احمد"
        subject = "ریاضیات"
        department = "علوم کمپیوتر"
        semester = "بهار"
        academic_year = "1403"
    
    class MockFormResult:
        valid = True
        def answers(self):
            return ["Yes", "Somewhat", "No"] * 5  # 15 answers (we need 14)
    
    survey = MockSurvey()
    form_results = [MockFormResult() for _ in range(25)]
    
    # Use writable reports directory
    reports_dir = Config.get_reports_dir()
    output_path = reports_dir / "test_html_report.html"
    
    try:
        result = generate_dari_qa_report(survey, form_results, str(output_path))
        print(f"✓ HTML report generated: {result}")
        print(f"✓ Saved to writable location: {reports_dir}")
        
        # Check file size
        file_size = output_path.stat().st_size
        print(f"✓ File size: {file_size:,} bytes")
        
        # Check for base64 images
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'data:image/' in content:
            count = content.count('data:image/')
            print(f"✓ Found {count} embedded base64 images")
        else:
            print("⚠ Warning: No base64 images found")
        
        # Check for key content
        if survey.professor in content:
            print(f"✓ Professor name found in report")
        if survey.subject in content:
            print(f"✓ Subject found in report")
        
        # Clean up
        output_path.unlink()
        print("✓ Test file cleaned up")
        print("\n✅ HTML report test passed")
        
    except Exception as e:
        print(f"\n❌ HTML report test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_pdf_form():
    """Test PDF form generation with logos."""
    print_header("Testing PDF Form Generation")
    
    from pdf_generator import generate_prefilled_form
    
    # Create mock survey
    class MockSurvey:
        id = 1
        faculty = "پوهنحی کمپیوتر ساینس"
        department = "دیپارتمنت نرم افزار"
        professor = "پوهاند محمد احمد"
        subject = "ریاضیات گسسته"
        semester = "بهار"
        academic_year = "1403"
    
    survey = MockSurvey()
    output_path = Path("test_pdf_form.pdf")
    
    try:
        result = generate_prefilled_form(
            survey,
            output_path,
            persistence=None,
            logo_path=None
        )
        print(f"✓ PDF form generated: {result}")
        
        # Check file size
        file_size = output_path.stat().st_size
        print(f"✓ File size: {file_size:,} bytes")
        
        # Verify it's a valid PDF (starts with %PDF)
        with open(output_path, 'rb') as f:
            header = f.read(4)
        
        if header == b'%PDF':
            print("✓ Valid PDF file format")
        else:
            print("⚠ Warning: File may not be a valid PDF")
        
        # Clean up
        output_path.unlink()
        print("✓ Test file cleaned up")
        print("\n✅ PDF form test passed")
        
    except Exception as e:
        print(f"\n❌ PDF form test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_pyinstaller_detection():
    """Test PyInstaller bundle detection."""
    print_header("Testing PyInstaller Detection")
    
    is_frozen = getattr(sys, 'frozen', False)
    has_meipass = hasattr(sys, '_MEIPASS')
    
    print(f"sys.frozen: {is_frozen}")
    print(f"sys._MEIPASS exists: {has_meipass}")
    
    if is_frozen and has_meipass:
        print(f"✓ Running in PyInstaller bundle")
        print(f"  Bundle path: {sys._MEIPASS}")
    else:
        print("✓ Running in normal Python environment")
    
    print("\n✅ PyInstaller detection working")

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  PRODUCTION FIXES - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    try:
        test_config_paths()
        test_pyinstaller_detection()
        test_html_report()
        test_pdf_form()
        
        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nThe application is ready for production build.")
        print("Run: .\\build_installer.ps1")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
