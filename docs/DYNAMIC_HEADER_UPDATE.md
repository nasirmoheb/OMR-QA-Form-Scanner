# Dynamic University and Faculty Names in Report Header

## Change Summary

Updated the Dari QA report template to use dynamic university and faculty names from the survey data instead of hardcoded values.

## Changes Made

### 1. Updated `src/report_generator.py`

Added university and faculty to metadata:

```python
metadata = {
    "university": survey.university or "پوهنتون بدخشان",
    "faculty": survey.faculty or "پوهنحی کمپیوتر ساینس",
    "teacher_name": survey.professor or "نامعلوم",
    "subject": survey.subject or "نامعلوم",
    "department": survey.department or "نامعلوم",
    "semester": f"{survey.semester} / {survey.academic_year}",
    "total_students": to_persian_num(total_students),
    "total_students_raw": total_students
}
```

**Default Values:**
- University: `پوهنتون بدخشان` (Badakhshan University)
- Faculty: `پوهنحی کمپیوتر ساینس` (Computer Science Faculty)

### 2. Updated `src/templates/qa_template.html`

#### Page 1 Header
```html
<!-- Before -->
<h1>وزارت تحصیلات عالی - پوهنتون بدخشان</h1>
<h2>پوهنحی کمپیوتر ساینس | کمیته ارتقای کیفیت</h2>

<!-- After -->
<h1>وزارت تحصیلات عالی - {{ meta.university }}</h1>
<h2>{{ meta.faculty }} | کمیته ارتقای کیفیت</h2>
```

#### Page 2 Footer (Credit)
```html
<!-- Before -->
<span>پوهنتون بدخشان</span>

<!-- After -->
<span>{{ meta.university }}</span>
```

### 3. Updated Test Files

Updated all test files to include university and faculty fields:
- `test_visual_report.py`
- `test_report_fix.py`
- `test_all_file_writes.py`
- `test_all_fixes.py`
- `test_writable_reports.py`

## Data Flow

```
Survey Object (from database)
    ↓
    university: "پوهنتون بدخشان"
    faculty: "پوهنحی کمپیوتر ساینس"
    ↓
report_generator.py (metadata)
    ↓
    meta.university
    meta.faculty
    ↓
qa_template.html (Jinja2 template)
    ↓
    {{ meta.university }}
    {{ meta.faculty }}
    ↓
Generated HTML Report
```

## Survey Model Fields

The Survey model includes:
```python
@dataclass
class Survey:
    university: str = ""
    faculty: str = ""
    department: str = ""
    subject: str = ""
    professor: str = ""
    semester: str = ""
    academic_year: str = ""
    # ... other fields
```

## Benefits

### 1. Flexibility
- Different universities can use the system
- Different faculties can generate reports
- No need to modify template for each institution

### 2. Accuracy
- Report header matches actual survey data
- No hardcoded values that might be incorrect
- Consistent with database records

### 3. Scalability
- System can be deployed to multiple universities
- Each institution sees their own name
- Easy to customize per deployment

### 4. Maintainability
- Single source of truth (database)
- No need to update template for different institutions
- Changes in university/faculty name automatically reflected

## Default Values

If survey data is missing, defaults are used:

| Field | Default Value | Translation |
|-------|---------------|-------------|
| university | پوهنتون بدخشان | Badakhshan University |
| faculty | پوهنحی کمپیوتر ساینس | Computer Science Faculty |

## Example Output

### Report Header (Page 1)
```
┌─────────────────────────────────────────────┐
│ [Logo]                                [Logo]│
│                                             │
│   وزارت تحصیلات عالی - پوهنتون بدخشان      │
│   پوهنحی کمپیوتر ساینس | کمیته ارتقای کیفیت│
│   گزارش تحلیل پیشرفته ارزیابی استاد...     │
│                                             │
└─────────────────────────────────────────────┘
```

### Credit Footer (Page 2)
```
سیستم تحلیل تضمین کیفیت • طراحی و توسعه: نصیر احمد محب • پوهنتون بدخشان
```

## Testing

### Test with Default Values
```python
class MockSurvey:
    university = "پوهنتون بدخشان"
    faculty = "پوهنحی کمپیوتر ساینس"
    # ... other fields
```

### Test with Custom Values
```python
class MockSurvey:
    university = "پوهنتون کابل"
    faculty = "پوهنحی انجنیری"
    # ... other fields
```

### Run Tests
```powershell
.\venv\Scripts\python.exe test_visual_report.py
.\venv\Scripts\python.exe test_all_fixes.py
```

**Result**: ✅ All tests passing

## Database Integration

When creating a survey in the application:

```python
survey = Survey(
    university="پوهنتون بدخشان",
    faculty="پوهنحی کمپیوتر ساینس",
    department="دیپارتمنت نرم افزار",
    subject="ریاضیات گسسته",
    professor="پوهاند محمد احمد",
    semester="بهار",
    academic_year="1403"
)
```

The report will automatically use these values in the header.

## Configuration

### Settings Integration

The university name can also be read from app settings:

```python
# In config.py
DEFAULT_UNIVERSITY_NAME: str = "پوهنتون بدخشان"

# In report_generator.py
metadata = {
    "university": survey.university or Config.DEFAULT_UNIVERSITY_NAME,
    # ...
}
```

### Future Enhancement

Add settings page to configure:
- Default university name
- Default faculty name
- Ministry header text
- Logo images

## Backward Compatibility

✅ **Fully backward compatible**
- Existing surveys without university/faculty will use defaults
- No database migration required
- Old reports remain valid

## Multi-Institution Support

This change enables:
- ✅ Multiple universities using the same system
- ✅ Multiple faculties within a university
- ✅ Customized reports per institution
- ✅ Centralized deployment with institution-specific branding

## Summary

### Before
- ❌ Hardcoded: `پوهنتون بدخشان`
- ❌ Hardcoded: `پوهنحی کمپیوتر ساینس`
- ❌ Not flexible for other institutions

### After
- ✅ Dynamic: `{{ meta.university }}`
- ✅ Dynamic: `{{ meta.faculty }}`
- ✅ Flexible for any institution
- ✅ Defaults to Badakhshan University if not specified

### Files Modified
1. `src/report_generator.py` - Added university and faculty to metadata
2. `src/templates/qa_template.html` - Use dynamic values in header
3. Test files - Updated mock objects

### Tests Status
- ✅ All tests passing
- ✅ Report generation working
- ✅ Dynamic values displaying correctly

---

**Status**: ✅ Complete
**Version**: 1.0.4
**Impact**: All Dari QA reports
**Backward Compatible**: Yes
