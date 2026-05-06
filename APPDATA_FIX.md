# Database Path Fix - Windows AppData

## Problem
The application was trying to create the database in `C:\Program Files\OMR QA Form Scanner\data\`, which requires administrator privileges and causes a **PermissionError: [WinError 5] Access is denied** error.

## Solution
Updated `src/persistence.py` to store the database in the user's AppData directory instead of Program Files:

### New Database Locations:
- **Windows (Installed)**: `%LOCALAPPDATA%\OMR_QA_Scanner\data\omr.db`
  - Example: `C:\Users\YourName\AppData\Local\OMR_QA_Scanner\data\omr.db`
- **Development Mode**: `./data/omr.db` (unchanged)

### Changes Made:
1. Added `_get_default_db_path()` function that:
   - Detects if running as a PyInstaller executable (`sys.frozen`)
   - Uses `%LOCALAPPDATA%` on Windows for installed apps
   - Falls back to local `./data/` directory for development

2. The database directory is automatically created with proper permissions

## Benefits:
✅ **No admin rights required** - Users can run the app normally  
✅ **Per-user data** - Each Windows user has their own database  
✅ **Windows best practices** - Follows Microsoft guidelines for application data  
✅ **Portable mode still works** - Development mode unchanged  

## Testing the Fix:

### 1. Uninstall the old version (if installed):
```powershell
# Go to Windows Settings > Apps > Installed Apps
# Find "OMR QA Form Scanner" and uninstall it
```

### 2. Install the new version:
```powershell
.\installer_output\OMR_Scanner_Setup_v1.0.0.exe
```

### 3. Run the application:
- The app should launch without errors
- Database will be created at: `C:\Users\<YourUsername>\AppData\Local\OMR_QA_Scanner\data\omr.db`

### 4. Verify the database location:
```powershell
# Check if the database was created
dir "$env:LOCALAPPDATA\OMR_QA_Scanner\data\"
```

You should see `omr.db` file created there.

## Installer Details:
- **File**: `installer_output\OMR_Scanner_Setup_v1.0.0.exe`
- **Size**: ~72 MB (compressed)
- **Build Date**: Latest
- **Changes**: Database path fix + 64-bit Windows detection fix

## Notes:
- The installer still requires admin rights to install to `C:\Program Files\`, but the **application itself runs without admin rights**
- All user data (surveys, form results, settings) is stored in the user's AppData folder
- Uninstalling the app will remove the program files but preserve user data in AppData (you can manually delete `%LOCALAPPDATA%\OMR_QA_Scanner` if needed)
