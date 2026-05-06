# Quick Fix Reference

## 🔧 What Was Fixed

### Issue #1: "Requires 64-bit Windows" Error
- **Fixed in**: `installer.iss`
- **Change**: `Is64BitInstallMode` → `IsWin64`

### Issue #2: "Access Denied" Error on Startup
- **Fixed in**: `src/persistence.py`
- **Change**: Database moved from `C:\Program Files\` → `%LOCALAPPDATA%\OMR_QA_Scanner\`

---

## 📦 New Installer

**File**: `installer_output\OMR_Scanner_Setup_v1.0.0.exe`  
**Size**: 72.42 MB  
**Status**: ✅ Ready to install

---

## 🚀 Quick Install

```powershell
# 1. Uninstall old version (if exists)
# Settings → Apps → Uninstall "OMR QA Form Scanner"

# 2. Install new version
.\installer_output\OMR_Scanner_Setup_v1.0.0.exe

# 3. Launch and test
# Desktop shortcut or Start Menu
```

---

## 📍 Database Location

**Old (broken)**: `C:\Program Files\OMR QA Form Scanner\data\omr.db` ❌  
**New (working)**: `C:\Users\<You>\AppData\Local\OMR_QA_Scanner\data\omr.db` ✅

Check it:
```powershell
dir "$env:LOCALAPPDATA\OMR_QA_Scanner\data\"
```

---

## ✅ Test Checklist

1. [ ] Installer runs without "64-bit" error
2. [ ] App launches without "Access Denied" error
3. [ ] Database file created in AppData
4. [ ] Can create a new survey
5. [ ] Can process forms
6. [ ] Can generate reports

---

## 🆘 If Problems Persist

1. **Check antivirus** - May be blocking the app
2. **Run as admin once** - To create initial folders
3. **Verify AppData access**:
   ```powershell
   Test-Path "$env:LOCALAPPDATA"
   ```

---

## 📚 Full Documentation

- **Detailed fix explanation**: `APPDATA_FIX.md`
- **Complete installation guide**: `INSTALLATION_FIXES_SUMMARY.md`
- **Build instructions**: `BUILD_INSTRUCTIONS.md`
- **Deployment guide**: `DEPLOYMENT_GUIDE.md`
