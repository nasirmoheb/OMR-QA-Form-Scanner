# Quick Build Guide - Production Installer

## ✅ Pre-Build Checklist

- [x] Template not found error - FIXED
- [x] Logos not showing in HTML reports - FIXED  
- [x] Logos not showing in PDF forms - FIXED
- [x] Permission denied when saving reports - FIXED
- [x] All tests passing

## 🚀 Build Steps

### 1. Run Tests (Recommended)
```powershell
.\venv\Scripts\python.exe test_all_fixes.py
```

Expected output:
```
✅ ALL TESTS PASSED!
The application is ready for production build.
```

### 2. Build Installer
```powershell
.\build_installer.ps1
```

This will:
1. Install/update PyInstaller
2. Clean previous builds
3. Run PyInstaller (creates `dist/Tadris_QA/`)
4. Run Inno Setup (creates installer)

### 3. Output Location
```
installer_output/Tadris_QA_Setup_v1.0.0.exe
```

## 🧪 Test the Installer

### On Development Machine
```powershell
# Install to a test location
.\installer_output\Tadris_QA_Setup_v1.0.0.exe

# Launch and verify:
# 1. Application starts
# 2. Generate HTML report → logos appear
# 3. Generate PDF form → logos appear
# 4. No console errors
```

### On Clean Windows VM (Recommended)
1. Copy installer to VM
2. Install (no Python required)
3. Test all features
4. Verify logos display correctly

## 📋 What Was Fixed

| Issue | Status | Solution |
|-------|--------|----------|
| Template not found | ✅ Fixed | Added `src/templates` to bundle |
| HTML logos missing | ✅ Fixed | Embedded as base64 data URIs |
| PDF logos missing | ✅ Fixed | Use Config paths with PyInstaller support |

## 🔍 Verification Commands

```powershell
# Check template exists in bundle
Test-Path "dist\Tadris_QA\_internal\src\templates\qa_template.html"

# Check logos exist in bundle
Test-Path "dist\Tadris_QA\_internal\assets\uni_logo.png"
Test-Path "dist\Tadris_QA\_internal\assets\mohe_logo.png"

# Check installer was created
Test-Path "installer_output\Tadris_QA_Setup_v1.0.0.exe"
```

## 📦 Distribution

The installer is now ready to distribute:
- **File**: `installer_output/Tadris_QA_Setup_v1.0.0.exe`
- **Size**: ~60-80 MB (compressed)
- **Requirements**: Windows 10/11 (64-bit)
- **No Python needed**: Fully standalone

## 🆘 Quick Troubleshooting

### Build fails
```powershell
# Clean and rebuild
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
.\build_installer.ps1
```

### Logos still missing after build
```powershell
# Verify logo files exist
Get-ChildItem assets\*.png

# Should show:
# uni_logo.png
# mohe_logo.png
```

### Template error persists
```powershell
# Check template file
Test-Path "src\templates\qa_template.html"

# Rebuild with clean flag
.\venv\Scripts\pyinstaller.exe build.spec --clean --noconfirm
```

## 📚 Documentation

- **Detailed fixes**: See `PRODUCTION_FIXES.md`
- **Summary**: See `FIXES_SUMMARY.md`
- **Build instructions**: See `BUILD_INSTRUCTIONS.md`

## ✨ Done!

Your production installer is ready with:
- ✅ Working templates
- ✅ Embedded logos in HTML reports
- ✅ Embedded logos in PDF forms
- ✅ PyInstaller bundle compatibility
- ✅ All tests passing

Distribute `installer_output/Tadris_QA_Setup_v1.0.0.exe` to users!
