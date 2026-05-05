# Building the Windows Installer

This guide shows how to create a standalone Windows installer (`.exe`) for the OMR QA Form Scanner.

---

## Prerequisites

### 1. Python Environment
Your existing `venv` with all dependencies installed:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Inno Setup (for installer creation)
Download and install from: **https://jrsoftware.org/isdl.php**

Default install path: `C:\Program Files (x86)\Inno Setup 6\`

---

## Quick Build (One Command)

From the project root in **PowerShell**:

```powershell
.\build_installer.ps1
```

This script:
1. Installs PyInstaller into your venv
2. Cleans previous build artifacts
3. Runs PyInstaller to create `dist/OMR_Scanner/` folder with the exe
4. Runs Inno Setup to wrap it into a single installer

**Output:**
- `installer_output/OMR_Scanner_Setup_v1.0.0.exe` — ready to distribute

---

## Manual Build (Step by Step)

If you prefer to run each step manually:

### Step 1: Install PyInstaller
```powershell
venv\Scripts\pip install pyinstaller
```

### Step 2: Build the EXE
```powershell
venv\Scripts\pyinstaller build.spec --noconfirm
```

This creates:
- `dist/OMR_Scanner/` — folder containing the exe and all dependencies
- `dist/OMR_Scanner/OMR_Scanner.exe` — the main executable

You can test it directly:
```powershell
.\dist\OMR_Scanner\OMR_Scanner.exe
```

### Step 3: Create the Installer
```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

This creates:
- `installer_output/OMR_Scanner_Setup_v1.0.0.exe`

---

## Customization

### Change App Icon
1. Create or obtain an `.ico` file (256x256 recommended)
2. Save it as `assets/icon.ico`
3. Uncomment these lines in `build.spec`:
   ```python
   # icon="assets/icon.ico",
   ```
4. Uncomment these lines in `installer.iss`:
   ```ini
   ; SetupIconFile=assets\icon.ico
   ; UninstallDisplayIcon={app}\{#AppExeName}
   ```

### Change Version Number
Edit `installer.iss`:
```ini
#define AppVersion   "1.0.0"
```

### Change Publisher / URL
Edit `installer.iss`:
```ini
#define AppPublisher "Your Organization"
#define AppURL       "https://your-org.example.com"
```

### Regenerate App GUID
Open `installer.iss` in Inno Setup IDE → Tools → Generate GUID → replace the existing one:
```ini
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
```

---

## Troubleshooting

### "PyInstaller not found"
```powershell
venv\Scripts\pip install pyinstaller
```

### "Inno Setup not found"
Download from https://jrsoftware.org/isdl.php and install.

If installed to a non-default path, pass it to the script:
```powershell
.\build_installer.ps1 -InnoSetup "D:\Tools\InnoSetup\ISCC.exe"
```

### "Module not found" errors when running the exe
Add the missing module to `hiddenimports` in `build.spec`:
```python
hidden = [
    # ... existing imports ...
    "your_missing_module",
]
```

### Exe is too large (>200 MB)
PyInstaller bundles the entire Python runtime + all dependencies. To reduce size:
1. Remove unused packages from `requirements.txt`
2. Add more exclusions to `build.spec`:
   ```python
   excludes=[
       "pytest", "hypothesis", "matplotlib", "scipy",
       # add more here
   ],
   ```
3. Enable UPX compression (already enabled in `build.spec`)

### Database not writable after install
The app creates `data/omr.db` in the install directory. If installed to `Program Files`, Windows requires admin rights to write there.

**Solution:** Move the database to user AppData:
1. Edit `src/persistence.py`:
   ```python
   import os
   from pathlib import Path
   
   # Use AppData instead of install dir
   DEFAULT_DB_PATH = Path(os.getenv("APPDATA")) / "OMR_Scanner" / "omr.db"
   ```

---

## Distribution

The final installer is a single `.exe` file:
```
installer_output/OMR_Scanner_Setup_v1.0.0.exe
```

Users can:
1. Double-click to install
2. Choose install location (default: `C:\Program Files\OMR QA Form Scanner\`)
3. Optionally create desktop shortcut
4. Launch the app from Start Menu or desktop

**Uninstall:** Via Windows Settings → Apps → OMR QA Form Scanner → Uninstall

---

## File Sizes (Approximate)

- PyInstaller output folder: ~180 MB
- Final installer (compressed): ~60-80 MB
- Installed size: ~180 MB

---

## Testing the Installer

Before distributing:
1. Build the installer
2. Test on a **clean Windows 10/11 VM** (no Python installed)
3. Install the app
4. Run it and verify all features work
5. Check that the database is created and writable
6. Test uninstall

---

## CI/CD Integration

To automate builds in GitHub Actions / Azure Pipelines:

```yaml
- name: Build Windows Installer
  run: |
    python -m pip install pyinstaller
    pyinstaller build.spec --noconfirm
    choco install innosetup -y
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
  
- name: Upload Installer
  uses: actions/upload-artifact@v3
  with:
    name: OMR-Scanner-Installer
    path: installer_output/*.exe
```

---

## Support

For build issues, check:
- PyInstaller docs: https://pyinstaller.org/
- Inno Setup docs: https://jrsoftware.org/ishelp/
- CustomTkinter packaging: https://github.com/TomSchimansky/CustomTkinter/wiki/Packaging
