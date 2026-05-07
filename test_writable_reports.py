"""Test that reports can be written to a writable location."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import Config

def test_reports_directory():
    """Test that reports directory is writable."""
    print("Testing reports directory...")
    
    reports_dir = Config.get_reports_dir()
    print(f"Reports directory: {reports_dir}")
    
    # Check if directory exists
    assert reports_dir.exists(), f"Reports directory doesn't exist: {reports_dir}"
    print(f"✓ Directory exists")
    
    # Test write permissions
    test_file = reports_dir / "test_write.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("Test write permissions")
        print(f"✓ Directory is writable")
        
        # Clean up
        test_file.unlink()
        print(f"✓ Test file cleaned up")
        
    except PermissionError as e:
        print(f"✗ Permission denied: {e}")
        raise
    
    print("\n✅ Reports directory is writable")

def test_report_generation_to_writable_location():
    """Test that report can be generated to writable location."""
    print("\nTesting report generation to writable location...")
    
    from report_generator import generate_dari_qa_report
    
    # Create mock objects
    class MockSurvey:
        professor = "Test Professor"
        subject = "Test Subject"
        department = "Test Department"
        semester = "Spring"
        academic_year = "2024"
    
    class MockFormResult:
        valid = True
        def answers(self):
            return ["Yes"] * 14
    
    survey = MockSurvey()
    form_results = [MockFormResult() for _ in range(10)]
    
    # Use the writable reports directory
    reports_dir = Config.get_reports_dir()
    output_path = reports_dir / "test_dari_qa_report.html"
    
    try:
        result = generate_dari_qa_report(survey, form_results, str(output_path))
        print(f"✓ Report generated: {result}")
        
        # Verify file exists
        assert output_path.exists(), "Report file was not created"
        print(f"✓ Report file exists")
        
        # Check file size
        file_size = output_path.stat().st_size
        print(f"✓ File size: {file_size:,} bytes")
        
        # Clean up
        output_path.unlink()
        print(f"✓ Test report cleaned up")
        
        print("\n✅ Report generation to writable location works")
        
    except PermissionError as e:
        print(f"\n❌ Permission error: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_frozen_mode_simulation():
    """Test what happens in frozen (PyInstaller) mode."""
    print("\nTesting frozen mode behavior...")
    
    # Save original state
    original_frozen = getattr(sys, 'frozen', False)
    
    # Simulate frozen mode
    sys.frozen = True
    
    try:
        reports_dir = Config.get_reports_dir()
        print(f"Frozen mode reports directory: {reports_dir}")
        
        # Should be in Documents folder
        if sys.platform == 'win32':
            expected_parent = Path.home() / "Documents"
            assert expected_parent in reports_dir.parents, \
                f"Expected reports dir in Documents, got: {reports_dir}"
            print(f"✓ Reports directory is in Documents folder")
        
        print("\n✅ Frozen mode simulation passed")
        
    finally:
        # Restore original state
        if original_frozen:
            sys.frozen = original_frozen
        else:
            delattr(sys, 'frozen')

if __name__ == "__main__":
    print("=" * 70)
    print("  WRITABLE REPORTS DIRECTORY TEST")
    print("=" * 70)
    
    test_reports_directory()
    test_report_generation_to_writable_location()
    test_frozen_mode_simulation()
    
    print("\n" + "=" * 70)
    print("  ✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nReports will be saved to:")
    print(f"  Development: {Config.ASSETS_DIR}")
    print(f"  Production:  {Path.home() / 'Documents' / 'Tadris_QA' / 'Reports'}")
