"""Comprehensive test for all file write operations to ensure they use writable locations."""

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

def test_dari_qa_report():
    """Test Dari QA report generation."""
    print_header("Testing Dari QA Report")
    
    from report_generator import generate_dari_qa_report
    
    class MockSurvey:
        professor = "Test"
        subject = "Test"
        department = "Test"
        semester = "Test"
        academic_year = "2024"
    
    class MockFormResult:
        valid = True
        def answers(self):
            return ["Yes"] * 14
    
    reports_dir = Config.get_reports_dir()
    output_path = reports_dir / "test_dari_qa.html"
    
    try:
        generate_dari_qa_report(MockSurvey(), [MockFormResult()], str(output_path))
        assert output_path.exists()
        print(f"✓ Dari QA report saved to: {output_path}")
        output_path.unlink()
        print("✓ Test file cleaned up")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        raise

def test_analytics_html_report():
    """Test analytics HTML report generation."""
    print_header("Testing Analytics HTML Report")
    
    from analytics_engine import AnalyticsEngine
    import pandas as pd
    
    engine = AnalyticsEngine()
    
    # Create proper DataFrame with all 14 questions
    data = {
        "Form_ID": ["f1", "f2"],
        "Form_Score": [100, 50],
        "Valid": [True, True]
    }
    for i in range(1, 15):
        data[f"Q{i}"] = ["Yes", "No"]
    
    df = pd.DataFrame(data)
    
    reports_dir = Config.get_reports_dir()
    output_path = reports_dir / "test_analytics.html"
    
    try:
        result = engine.generate_report(df, output_path=str(output_path))
        assert Path(result).exists()
        print(f"✓ Analytics report saved to: {result}")
        Path(result).unlink()
        print("✓ Test file cleaned up")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        raise

def test_analytics_default_path():
    """Test analytics report with default path (no output_path specified)."""
    print_header("Testing Analytics Report Default Path")
    
    from analytics_engine import AnalyticsEngine
    import pandas as pd
    
    engine = AnalyticsEngine()
    
    # Create proper DataFrame with all 14 questions
    data = {
        "Form_ID": ["f1"],
        "Form_Score": [100],
        "Valid": [True]
    }
    for i in range(1, 15):
        data[f"Q{i}"] = ["Yes"]
    
    df = pd.DataFrame(data)
    
    try:
        # Call without output_path - should use writable directory
        result = engine.generate_report(df)
        result_path = Path(result)
        assert result_path.exists()
        print(f"✓ Default report saved to: {result}")
        
        # Verify it's in a writable location (not Program Files)
        if sys.platform == 'win32' and 'Program Files' in str(result_path):
            print(f"✗ ERROR: Report saved to Program Files: {result_path}")
            raise AssertionError("Report should not be saved to Program Files")
        
        print("✓ Report is in writable location")
        result_path.unlink()
        print("✓ Test file cleaned up")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        raise

def test_csv_export():
    """Test CSV export (uses file dialog, so just test the function)."""
    print_header("Testing CSV Export")
    
    from analytics_engine import AnalyticsEngine
    
    class MockFormResult:
        def answers(self):
            return ["Yes"] * 14
    
    engine = AnalyticsEngine()
    reports_dir = Config.get_reports_dir()
    output_path = reports_dir / "test_export.csv"
    
    try:
        result = engine.export_csv([MockFormResult()], str(output_path))
        assert Path(result).exists()
        print(f"✓ CSV exported to: {result}")
        Path(result).unlink()
        print("✓ Test file cleaned up")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        raise

def test_advanced_html_report():
    """Test advanced HTML report generation."""
    print_header("Testing Advanced HTML Report")
    
    from plotly_generator import PlotlyGenerator
    import pandas as pd
    
    # Create proper DataFrame with all 14 questions
    data = {
        "Form_ID": ["f1", "f2"],
        "Form_Score": [100, 50],
        "Valid": [True, True]
    }
    for i in range(1, 15):
        data[f"Q{i}"] = ["Yes", "No"]
    
    df = pd.DataFrame(data)
    
    html = PlotlyGenerator.generate_dashboard_html(df, 75.0, mode="advanced")
    
    reports_dir = Config.get_reports_dir()
    output_path = reports_dir / "test_advanced.html"
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        assert output_path.exists()
        print(f"✓ Advanced report saved to: {output_path}")
        output_path.unlink()
        print("✓ Test file cleaned up")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        raise

def test_reports_directory_location():
    """Verify reports directory is in a writable location."""
    print_header("Testing Reports Directory Location")
    
    reports_dir = Config.get_reports_dir()
    print(f"Reports directory: {reports_dir}")
    
    # In production (frozen), should be in Documents
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            expected_parent = Path.home() / "Documents"
            if expected_parent not in reports_dir.parents:
                print(f"✗ ERROR: Reports dir should be in Documents")
                raise AssertionError("Reports directory not in Documents folder")
        print("✓ Reports directory is in user's Documents folder")
    else:
        print("✓ Development mode: using assets folder")
    
    # Verify it's writable
    test_file = reports_dir / "test_write.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        test_file.unlink()
        print("✓ Reports directory is writable")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        raise

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  FILE WRITE OPERATIONS - COMPREHENSIVE TEST")
    print("=" * 70)
    
    try:
        test_reports_directory_location()
        test_dari_qa_report()
        test_analytics_html_report()
        test_analytics_default_path()
        test_csv_export()
        test_advanced_html_report()
        
        print("\n" + "=" * 70)
        print("  ✅ ALL FILE WRITE TESTS PASSED!")
        print("=" * 70)
        print("\n✅ No permission errors detected")
        print("✅ All reports save to writable locations")
        print(f"\nReports location: {Config.get_reports_dir()}")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("  ❌ TESTS FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
