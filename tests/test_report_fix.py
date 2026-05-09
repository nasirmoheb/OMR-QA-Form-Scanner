"""Test script to verify report generation works with bundled paths."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import Config
from report_generator import generate_dari_qa_report

def test_paths():
    """Test that all required paths exist."""
    print("Testing paths...")
    print(f"PROJECT_ROOT: {Config.PROJECT_ROOT}")
    print(f"ASSETS_DIR: {Config.ASSETS_DIR}")
    print(f"TEMPLATES_DIR: {Config.TEMPLATES_DIR}")
    print(f"DEFAULT_LOGO_PATH: {Config.DEFAULT_LOGO_PATH}")
    print(f"QA_LOGO_PATH: {Config.QA_LOGO_PATH}")
    
    assert Config.ASSETS_DIR.exists(), f"Assets directory not found: {Config.ASSETS_DIR}"
    assert Config.TEMPLATES_DIR.exists(), f"Templates directory not found: {Config.TEMPLATES_DIR}"
    assert Config.DEFAULT_LOGO_PATH.exists(), f"University logo not found: {Config.DEFAULT_LOGO_PATH}"
    assert Config.QA_LOGO_PATH.exists(), f"QA logo not found: {Config.QA_LOGO_PATH}"
    
    template_file = Config.TEMPLATES_DIR / "qa_template.html"
    assert template_file.exists(), f"Template file not found: {template_file}"
    
    print("✓ All paths exist")

def test_report_generation():
    """Test that report generation works."""
    print("\nTesting report generation...")
    
    # Create a mock survey object
    class MockSurvey:
        university = "پوهنتون بدخشان"
        faculty = "پوهنحی کمپیوتر ساینس"
        professor = "Test Professor"
        subject = "Test Subject"
        department = "Test Department"
        semester = "Spring"
        academic_year = "2024"
    
    # Create a mock form result
    class MockFormResult:
        valid = True
        def answers(self):
            return ["Yes"] * 14
    
    survey = MockSurvey()
    form_results = [MockFormResult() for _ in range(10)]
    output_path = Path("test_report.html")
    
    try:
        result = generate_dari_qa_report(survey, form_results, str(output_path))
        print(f"✓ Report generated: {result}")
        
        # Check that the HTML contains base64 images
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'data:image/' in content:
            print("✓ Logos embedded as base64")
        else:
            print("⚠ Warning: No base64 images found in HTML")
        
        # Clean up
        output_path.unlink()
        print("✓ Test report cleaned up")
        
    except Exception as e:
        print(f"✗ Error generating report: {e}")
        raise

if __name__ == "__main__":
    test_paths()
    test_report_generation()
    print("\n✅ All tests passed!")
