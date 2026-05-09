# System Credit Added to Reports

## Change Summary

Added developer credit to the Dari QA report template to acknowledge the system creator.

## Credit Text

**Arabic/Dari:**
```
سیستم تحلیل تضمین کیفیت • طراحی و توسعه: محب • پوهنتون بدخشان
```

**Translation:**
```
Quality Assurance Analysis System • Design and Development: Mahab • Badakhshan University
```

## Placement

### Page 1 (Bottom)
- Small, subtle credit below the main table
- Font size: 7.5pt
- Color: Light gray (#94a3b8)
- Format: `System Name • Developer: محب`

### Page 2 (Bottom)
- More detailed credit below signatures
- Font size: 8pt
- Color: Gray with blue highlight for name
- Format: `System Name • Developer: محب • University`

## Visual Style

```css
/* Page 1 Credit */
font-size: 7.5pt;
color: #94a3b8; /* Light gray */
text-align: center;

/* Page 2 Credit */
font-size: 8pt;
color: #64748b; /* Medium gray */
Developer name: #0369a1; /* Blue highlight */
font-weight: bold;
```

## Layout

### Page 1
```
┌─────────────────────────────────────┐
│                                     │
│   [Main Table Content]              │
│                                     │
│ ─────────────────────────────────── │
│ سیستم تحلیل تضمین کیفیت • محب      │
└─────────────────────────────────────┘
```

### Page 2
```
┌─────────────────────────────────────┐
│   [Signatures]                      │
│ ─────────────────────────────────── │
│ سیستم تحلیل تضمین کیفیت •          │
│ طراحی و توسعه: محب • پوهنتون بدخشان│
└─────────────────────────────────────┘
```

## Code Changes

### File Modified
`src/templates/qa_template.html`

### Page 1 Credit
```html
<div style="text-align: center; margin-top: 15px; font-size: 7.5pt; color: #94a3b8;">
    <span>سیستم تحلیل تضمین کیفیت</span>
    <span style="margin: 0 5px;">•</span>
    <span style="font-weight: bold; color: #0369a1;">طراحی و توسعه: محب</span>
</div>
```

### Page 2 Credit
```html
<div style="text-align: center; margin-top: 20px; padding-top: 10px; 
     border-top: 1px solid #e2e8f0; font-size: 8pt; color: #64748b;">
    <span style="font-weight: normal;">سیستم تحلیل تضمین کیفیت</span>
    <span style="margin: 0 5px;">•</span>
    <span style="font-weight: bold; color: #0369a1;">طراحی و توسعه: محب</span>
    <span style="margin: 0 5px;">•</span>
    <span>پوهنتون بدخشان</span>
</div>
```

## Design Principles

1. **Subtle**: Small font size, light colors - doesn't distract from main content
2. **Professional**: Clean, centered layout with proper spacing
3. **Respectful**: Acknowledges the creator without being intrusive
4. **Bilingual-Ready**: Uses Dari/Arabic script
5. **Print-Friendly**: Visible but not prominent in printed versions

## Testing

Generate a test report to verify:
```powershell
.\venv\Scripts\python.exe test_visual_report.py
```

### Verification
- [x] Credit visible on page 1 (bottom)
- [x] Credit visible on page 2 (bottom)
- [x] Text properly formatted in Dari
- [x] Colors appropriate (not too bold)
- [x] Doesn't interfere with main content
- [x] Visible in print preview

## Benefits

1. **Attribution**: Properly credits the system developer
2. **Professional**: Shows the system is officially developed
3. **Branding**: Associates the system with Badakhshan University
4. **Motivation**: Acknowledges the developer's work
5. **Traceability**: Users know who created the system

## Future Enhancements

Potential additions:
- [ ] Add version number
- [ ] Add development year
- [ ] Add contact information
- [ ] Add system logo/icon
- [ ] Make credit customizable via settings

## Summary

✅ **Credit added to both pages of the report**
- Page 1: Simple credit line
- Page 2: Detailed credit with university name
- Subtle, professional styling
- Properly formatted in Dari script

The system creator **محب** is now properly credited in all generated reports! 🎉

---

**Status**: ✅ Complete
**Developer**: محب
**Institution**: پوهنتون بدخشان (Badakhshan University)
