"""Generate a visual test report to verify the layout changes."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import Config
from report_generator import generate_dari_qa_report

def generate_test_report():
    """Generate a test report for visual inspection."""
    
    # Create mock survey
    class MockSurvey:
        university = "پوهنتون کابل"
        faculty = "پوهنحی کمپیوتر ساینس"
        professor = "پوهاند محمد احمد رحیمی"
        subject = "ریاضیات گسسته"
        department = "دیپارتمنت نرم افزار"
        semester = "بهار"
        academic_year = "1403"
    
    # Create mock form results with varied answers
    class MockFormResult:
        def __init__(self, valid=True, pattern=None):
            self.valid = valid
            self._pattern = pattern or ["Yes"] * 14
        
        def answers(self):
            return self._pattern
    
    # Create diverse results
    form_results = []
    
    # 15 students with "Yes" answers
    for i in range(15):
        form_results.append(MockFormResult(True, ["Yes"] * 14))
    
    # 8 students with "Somewhat" answers
    for i in range(8):
        form_results.append(MockFormResult(True, ["Somewhat"] * 14))
    
    # 3 students with "No" answers
    for i in range(3):
        form_results.append(MockFormResult(True, ["No"] * 14))
    
    # 2 students with mixed answers
    form_results.append(MockFormResult(True, ["Yes", "Yes", "Somewhat", "Yes", "No", "Yes", "Somewhat", "Yes", "Yes", "No", "Yes", "Yes", "Somewhat", "Yes"]))
    form_results.append(MockFormResult(True, ["Somewhat", "Yes", "Yes", "No", "Yes", "Somewhat", "Yes", "Yes", "Somewhat", "Yes", "No", "Yes", "Yes", "Somewhat"]))
    
    # 2 invalid forms
    form_results.append(MockFormResult(False, ["Invalid"] * 14))
    form_results.append(MockFormResult(False, ["Invalid"] * 14))
    
    survey = MockSurvey()
    
    # Generate to assets folder for easy viewing
    output_path = Config.ASSETS_DIR / "visual_test_report.html"
    
    try:
        result = generate_dari_qa_report(survey, form_results, str(output_path))
        print(f"✅ Test report generated successfully!")
        print(f"📄 Location: {result}")
        print(f"\n📋 Report Details:")
        print(f"   - Total forms: {len(form_results)}")
        print(f"   - Valid forms: {len([f for f in form_results if f.valid])}")
        print(f"   - Invalid forms: {len([f for f in form_results if not f.valid])}")
        print(f"\n🌐 Open in browser to verify:")
        print(f"   1. Second page has top margin")
        print(f"   2. Print dialog opens automatically")
        print(f"   3. All content fits on 2 pages (no third page)")
        print(f"   4. Signatures are on second page")
        
        # Open in browser
        import webbrowser
        webbrowser.open(f"file:///{output_path.resolve()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 70)
    print("  VISUAL TEST REPORT GENERATOR")
    print("=" * 70)
    generate_test_report()
