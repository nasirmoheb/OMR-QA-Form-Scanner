# Installation Fixes Summary

## Issues Fixed

### 1. ✅ 64-bit Windows Detection Error
**Problem**: Installer showed "This app requires 64-bit version of Windows" even on 64-bit systems.

**Solution**: 
- Changed detection function from `Is64BitInstallMode` to `IsWin64` in `installer.iss`
- Added proper architecture constraints:
  - `ArchitecturesAllowed=x64compatible`
  - `ArchitecturesInstallIn64BitMode=x64compatible`

**File Modified**: `installer.iss`

---

### 2. ✅ Permission Denied Error (WinError 5)
**Problem**: Application crashed on startup with:
```
PermissionError: [WinError 5] Access is denied: 'C:\\Program Files\\OMR QA Form Scanner\\data'
```

**Root Cause**: The app tried to create a database in `C:\Program Files\`, which requires admin privileges.

**Solution**: 
- Modified `src/persistence.py` to use Windows AppData directory
- Database now stored at: `%LOCALAPPDATA%\OMR_QA_Scanner\data\omr.db`
- Example: `C:\Users\YourName\AppData\Local\OMR_QA_Scanner\data\omr.db`

**Benefits**:
- ✅ No admin rights needed to run the app
- ✅ Per-user data isolation
- ✅ Follows Windows best practices
- ✅ Development mode unchanged

**File Modified**: `src/persistence.py`

---

## Rebuilt Files

### Executable
- **Location**: `dist\OMR_Scanner\`
- **Main File**: `dist\OMR_Scanner\OMR_Scanner.exe`
- **Size**: ~180 MB (uncompressed)

### Installer
- **Location**: `installer_output\OMR_Scanner_Setup_v1.0.0.exe`
- **Size**: 72.42 MB (LZMA2 compressed)
- **Target**: Windows 10+ (64-bit only)

---

## Installation Instructions

### Step 1: Uninstall Old Version (if installed)
1. Open Windows Settings → Apps → Installed Apps
2. Find "OMR QA Form Scanner"
3. Click Uninstall

### Step 2: Install New Version
1. Run: `installer_output\OMR_Scanner_Setup_v1.0.0.exe`
2. Follow the installation wizard
3. The installer will:
   - Install to `C:\Program Files\OMR QA Form Scanner\`
   - Create desktop shortcut (optional)
   - Create start menu entry

### Step 3: Launch Application
- Double-click the desktop shortcut, or
- Find it in Start Menu → OMR QA Form Scanner

### Step 4: Verify Installation
The app should launch without errors. Database will be created at:
```
C:\Users\<YourUsername>\AppData\Local\OMR_QA_Scanner\data\omr.db
```

To verify:
```powershell
dir "$env:LOCALAPPDATA\OMR_QA_Scanner\data\"
```

---

## Technical Details

### Database Path Logic
```python
def _get_default_db_path() -> Path:
    # Check if running as PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Production: Use AppData
        if os.name == 'nt':  # Windows
            return Path(os.environ['LOCALAPPDATA']) / "OMR_QA_Scanner" / "data" / "omr.db"
        else:  # Linux/Mac
            return Path.home() / ".local" / "share" / "OMR_QA_Scanner" / "data" / "omr.db"
    
    # Development: Use local directory
    return Path(__file__).parent.parent / "data" / "omr.db"
```

### Installer Configuration
```ini
[Setup]
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin  ; Only for installation, not for running

[Code]
function InitializeSetup(): Boolean;
begin
  if not IsWin64 then
  begin
    MsgBox('This application requires a 64-bit version of Windows.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
```

---

## Data Locations

### User Data (Surveys, Forms, Settings)
- **Windows**: `%LOCALAPPDATA%\OMR_QA_Scanner\data\omr.db`
- **Full Path**: `C:\Users\<Username>\AppData\Local\OMR_QA_Scanner\data\omr.db`

### Application Files
- **Installation**: `C:\Program Files\OMR QA Form Scanner\`
- **Executable**: `C:\Program Files\OMR QA Form Scanner\OMR_Scanner.exe`

### Uninstallation
- Program files are removed automatically
- User data in AppData is **preserved** (delete manually if needed)

---

## Testing Checklist

- [x] Installer runs on 64-bit Windows without errors
- [x] Application launches without permission errors
- [x] Database is created in AppData directory
- [ ] Create a new survey (test database write)
- [ ] Process forms (test image processing)
- [ ] Generate reports (test PDF generation)
- [ ] Close and reopen app (test data persistence)

---

## Troubleshooting

### If the app still shows permission errors:
1. Check if antivirus is blocking the app
2. Verify the AppData folder exists and is writable:
   ```powershell
   Test-Path "$env:LOCALAPPDATA\OMR_QA_Scanner"
   ```
3. Run as administrator (one time only) to create initial folders

### If the installer fails:
1. Ensure you have admin rights
2. Close any running instances of the app
3. Temporarily disable antivirus
4. Check Windows Event Viewer for detailed errors

---

## Version History

### v1.0.0 (Current)
- ✅ Fixed 64-bit Windows detection
- ✅ Fixed database permission error (moved to AppData)
- ✅ Circular checkbox design
- ✅ Mixed blue/black pen detection
- ✅ Reprocess button in dashboard
- ✅ Thin checkbox borders in PDF
- ✅ Calibrated grid dimensions

---

## Contact & Support

If you encounter any issues:
1. Check the log files in: `%LOCALAPPDATA%\OMR_QA_Scanner\logs\` (if logging is enabled)
2. Review this document for troubleshooting steps
3. Contact the development team with:
   - Windows version
   - Error message (screenshot)
   - Steps to reproduce
