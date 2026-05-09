# Production Installer Fixes

## Issues Fixed

### 1. Template Not Found Error
**Problem:** `'qa_template.html' not found in search path`

**Root Cause:** The Jinja2 template loader was using a relative path that didn't work in PyInstaller bundles.

**Solution:**
- Updated `src/config.py` to detect PyInstaller bundle mode using `sys._MEIPASS`
- Added `TEMPLATES_DIR` to Config that resolves correctly in both dev and production
- Updated `build.spec` to include `src/templates` directory in the bundle
- Modified `src/report_generator.py` to use `Config.TEMPLATES_DIR` instead of relative paths

### 2. Logos Not Displaying in HTML Reports
**Problem:** University and Ministry logos not showing in generated HTML reports

**Root Cause:** HTML template used relative paths (`uni_logo.png`, `mohe_logo.png`) that don't work when the HTML is opened in a browser from the bundled app.

**Solution:**
- Embedded logos as base64 data URIs directly in the HTML
- Added `_image_to_base64()` function in `src/report_generator.py`
- Updated `src/templates/qa_template.html` to use base64 data or fallback to relative paths
- Logos are now self-contained in the HTML file

### 3. Logos Not Displaying in PDF Forms
**Problem:** University and Ministry logos not showing in generated PDF survey forms

**Root Cause:** PDF generator was using `os.path.exists()` with string paths instead of using Config paths that handle PyInstaller bundles.

**Solution:**
- Updated `src/pdf_generator.py` to use `Config.DEFAULT_LOGO_PATH` and `Config.QA_LOGO_PATH`
- Changed to use `Path.exists()` method instead of `os.path.exists()`
- Ensured Config is imported early in the function to get correct paths
- Both logos now display correctly in bundled applications

## Files Modified

### 1. `src/config.py`
```python
# Added PyInstaller detection
@staticmethod
def _get_base_path() -> Path:
    """Get the base path for resources, handling PyInstaller bundled apps."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running in normal Python environment
        return Path(__file__).resolve().parent.parent

# Added TEMPLATES_DIR
TEMPLATES_DIR: Path = PROJECT_ROOT / "src" / "templates"
```

### 2. `src/report_generator.py`
```python
# Added base64 encoding function
def _image_to_base64(image_path):
    """Convert an image file to base64 data URI for embedding in HTML."""
    # ... implementation

# Updated template loading
from config import Config
template_dir = Config.TEMPLATES_DIR
env = Environment(loader=FileSystemLoader(str(template_dir)))

# Convert logos to base64
uni_logo_data = _image_to_base64(Config.DEFAULT_LOGO_PATH)
mohe_logo_data = _image_to_base64(Config.QA_LOGO_PATH)

# Pass to template
html_output = template.render(
    # ... other params
    uni_logo_data=uni_logo_data,
    mohe_logo_data=mohe_logo_data
)
```

### 3. `src/templates/qa_template.html`
```html
<!-- Updated logo references to use base64 data -->
<img src="{{ uni_logo_data if uni_logo_data else 'uni_logo.png' }}" alt="University Logo">
<img src="{{ mohe_logo_data if mohe_logo_data else 'mohe_logo.png' }}" alt="QA Logo">
```

### 4. `build.spec`
```python
# Added templates directory to bundled data
datas = [
    (str(CTK_PATH), "customtkinter"),
    (str(ASSETS), "assets"),
    (str(SRC / "templates"), "src/templates"),  # NEW
    (str(DATA_DIR), "data"),
]
```

### 5. `src/pdf_generator.py`
```python
# Updated logo path resolution to use Config
from config import Config

if logo_path is not None and Path(str(logo_path)).exists():
    resolved_logo = str(logo_path)
elif resolved_logo is None and Config.DEFAULT_LOGO_PATH.exists():
    resolved_logo = str(Config.DEFAULT_LOGO_PATH)

# Updated QA logo loading
if Config.QA_LOGO_PATH.exists():
    try:
        c.drawImage(
            str(Config.QA_LOGO_PATH),
            # ... drawing parameters
        )
```

## Testing

Two test scripts have been created to verify the fixes:

### 1. HTML Report Test (`test_report_fix.py`)
Verifies:
- All required paths exist
- Template directory is accessible
- Logo files are found
- HTML report generation works
- Logos are embedded as base64 in the HTML

Run the test:
```powershell
.\venv\Scripts\python.exe test_report_fix.py
```

### 2. PDF Form Test (`test_pdf_fix.py`)
Verifies:
- Logo paths are resolved correctly
- PDF form generation works
- Logos are embedded in the PDF
- File is created successfully

Run the test:
```powershell
.\venv\Scripts\python.exe test_pdf_fix.py
```

### Run All Tests
```powershell
.\venv\Scripts\python.exe test_report_fix.py
.\venv\Scripts\python.exe test_pdf_fix.py
```

## Rebuilding the Installer

After these fixes, rebuild the installer:

```powershell
.\build_installer.ps1
```

The installer will now:
- ✅ Include the templates directory
- ✅ Find the qa_template.html file
- ✅ Embed logos as base64 in generated HTML reports
- ✅ Display logos correctly in the browser
- ✅ Embed logos correctly in generated PDF forms
- ✅ Use correct paths in PyInstaller bundles

## Benefits

1. **Self-contained HTML reports**: HTML reports now contain embedded logos and work anywhere
2. **Correct PDF logos**: PDF forms display both university and ministry logos correctly
3. **No path dependencies**: Reports and PDFs don't rely on external image files
4. **Portable**: HTML reports can be emailed or moved without losing images
5. **Robust**: Works in both development and production environments
6. **PyInstaller compatible**: All paths resolve correctly in bundled applications

## Verification Checklist

After rebuilding, verify:
- [ ] Installer builds without errors
- [ ] Application launches successfully
- [ ] Generate a test HTML report
- [ ] Logos appear in the HTML report
- [ ] HTML report opens in browser correctly
- [ ] Generate a test PDF form
- [ ] Logos appear in the PDF form (both university and ministry)
- [ ] PDF opens correctly
- [ ] No console errors about missing files

## Technical Details

### PyInstaller Bundle Detection
When PyInstaller creates a bundle, it sets:
- `sys.frozen = True`
- `sys._MEIPASS = <temp_extraction_path>`

Our code detects this and uses `_MEIPASS` as the base path for resources.

### Base64 Encoding
Images are converted to base64 data URIs:
```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

This allows images to be embedded directly in HTML without external files.

### Fallback Behavior
The template uses conditional rendering:
```jinja2
{{ uni_logo_data if uni_logo_data else 'uni_logo.png' }}
```

If base64 encoding fails, it falls back to relative paths (useful for development).

## Troubleshooting

### If template still not found:
1. Check that `src/templates` exists in the dist folder
2. Verify `build.spec` includes the templates directory
3. Rebuild with `--clean` flag: `pyinstaller build.spec --clean --noconfirm`

### If logos still not showing:
1. Verify logo files exist in `assets/` directory
2. Check file permissions
3. Look for errors in the console output
4. Verify base64 data is in the generated HTML (open in text editor)

### If paths are wrong:
1. Check `Config.PROJECT_ROOT` value
2. Verify `sys._MEIPASS` is set correctly
3. Add debug logging to see resolved paths

## Future Improvements

Consider:
1. Caching base64-encoded logos to avoid re-encoding
2. Compressing images before encoding to reduce HTML size
3. Adding error handling for corrupted image files
4. Supporting custom logo uploads with validation
