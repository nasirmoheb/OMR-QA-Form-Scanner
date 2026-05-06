# OMR QA Scanner - Deployment Guide

## ✅ Build Complete!

Your Windows application has been successfully built and is ready for distribution.

---

## 📦 Available Distribution Options

### Option 1: Portable ZIP (✅ Ready Now)
**Location**: `portable_output/OMR_Scanner_Portable_v1.0.0.zip`  
**Size**: ~104 MB  
**Best for**: Quick deployment, USB drives, no admin rights needed

**How to use:**
1. Extract the ZIP to any folder
2. Run `OMR_Scanner.exe`
3. No installation required!

**Advantages:**
- ✅ No installation needed
- ✅ Works without admin rights
- ✅ Can run from USB drive
- ✅ Easy to update (just replace files)
- ✅ Multiple versions can coexist

**Disadvantages:**
- ❌ No Start Menu shortcut
- ❌ No desktop icon
- ❌ No automatic uninstaller
- ❌ Users must extract manually

---

### Option 2: Windows Installer (Requires Inno Setup)
**Location**: `installer_output/OMR_Scanner_Setup_v1.0.0.exe` (after building)  
**Size**: ~60-80 MB (compressed)  
**Best for**: Professional deployment, enterprise distribution

**To create the installer:**

1. **Download and install Inno Setup**:
   - Visit: https://jrsoftware.org/isdl.php
   - Download: Inno Setup 6.x
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

2. **Run the build script again**:
   ```powershell
   .\build_installer.ps1
   ```

3. **Or compile manually**:
   ```powershell
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

**Advantages:**
- ✅ Professional installer experience
- ✅ Start Menu shortcuts
- ✅ Desktop icon (optional)
- ✅ Proper uninstaller
- ✅ Smaller file size (compressed)
- ✅ Version management

**Disadvantages:**
- ❌ Requires admin rights to install
- ❌ Installs to Program Files
- ❌ Only one version at a time

---

## 📂 What Was Built

### Executable Folder
**Location**: `dist\OMR_Scanner\`  
**Contents**:
```
OMR_Scanner/
├── OMR_Scanner.exe          # Main application
├── python311.dll            # Python runtime
├── base_library.zip         # Python standard library
├── _internal/               # Dependencies and DLLs
│   ├── cv2/                 # OpenCV
│   ├── customtkinter/       # UI framework
│   ├── numpy/               # Numerical computing
│   ├── pandas/              # Data analysis
│   ├── plotly/              # Charts
│   ├── reportlab/           # PDF generation
│   └── ... (other dependencies)
├── assets/                  # App resources
│   ├── uni_logo.png
│   ├── mohe_logo.png
│   └── qa_template.html
└── data/                    # Database folder
    └── omr.db (created on first run)
```

**Total Size**: ~180 MB uncompressed

---

## 🚀 Distribution Methods

### Method 1: Direct File Sharing
**Best for**: Small teams, internal use

1. Share the portable ZIP file
2. Users extract and run
3. No IT support needed

**Distribution channels:**
- Email (if < 25 MB, split into parts)
- Shared network drive
- USB drives
- Cloud storage (Google Drive, Dropbox, OneDrive)

---

### Method 2: Web Download
**Best for**: Public distribution, large user base

1. Upload ZIP or installer to web server
2. Create download page with instructions
3. Users download and install

**Hosting options:**
- GitHub Releases (free, unlimited bandwidth)
- Organization website
- File hosting services

---

### Method 3: Network Deployment
**Best for**: Enterprise, multiple computers

1. Place installer on network share
2. Deploy via Group Policy or SCCM
3. Silent install: `OMR_Scanner_Setup.exe /VERYSILENT /NORESTART`

---

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10 (64-bit) or Windows 11
- **RAM**: 4 GB
- **Disk Space**: 250 MB
- **Display**: 1280x720 or higher
- **Scanner**: Any TWAIN-compatible scanner (optional)

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **Disk Space**: 500 MB
- **Display**: 1920x1080 or higher
- **Scanner**: Flatbed scanner with 300 DPI capability

### Dependencies
**All dependencies are bundled** — no separate installation needed:
- ✅ Python runtime (included)
- ✅ OpenCV (included)
- ✅ CustomTkinter (included)
- ✅ All other libraries (included)

**Users do NOT need to install:**
- ❌ Python
- ❌ Any Python packages
- ❌ Visual C++ Redistributables (bundled)

---

## 📝 User Instructions

### For Portable ZIP

**Installation:**
1. Download `OMR_Scanner_Portable_v1.0.0.zip`
2. Right-click → Extract All
3. Choose destination folder (e.g., `C:\OMR_Scanner`)
4. Open the extracted folder
5. Double-click `OMR_Scanner.exe`

**First Run:**
- Windows may show "Windows protected your PC" warning
- Click "More info" → "Run anyway"
- This is normal for unsigned applications

**Creating Desktop Shortcut:**
1. Right-click `OMR_Scanner.exe`
2. Send to → Desktop (create shortcut)

---

### For Windows Installer

**Installation:**
1. Download `OMR_Scanner_Setup_v1.0.0.exe`
2. Double-click to run
3. Follow installation wizard
4. Choose install location (default: `C:\Program Files\OMR QA Form Scanner`)
5. Optionally create desktop shortcut
6. Click Install

**First Run:**
- Find in Start Menu: "OMR QA Form Scanner"
- Or use desktop shortcut (if created)

**Uninstallation:**
- Windows Settings → Apps → OMR QA Form Scanner → Uninstall
- Or: Start Menu → OMR QA Form Scanner → Uninstall

---

## 🔧 Troubleshooting

### "Windows protected your PC" Warning
**Cause**: Application is not digitally signed  
**Solution**: Click "More info" → "Run anyway"

**To avoid this warning:**
- Purchase a code signing certificate (~$100-300/year)
- Sign the executable with `signtool.exe`

---

### "Application failed to start" Error
**Cause**: Missing Visual C++ Redistributables  
**Solution**: 
1. Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Install and restart

**Note**: This should not happen as redistributables are bundled, but some systems may need them.

---

### Database Permission Errors
**Cause**: App installed to Program Files, needs admin rights to write  
**Solution**: 
- Run as administrator (right-click → Run as administrator)
- Or: Install to user folder (e.g., `C:\Users\YourName\OMR_Scanner`)

---

### Slow Startup (First Run)
**Cause**: Windows Defender scanning the executable  
**Solution**: 
- Wait 30-60 seconds on first run
- Add to Windows Defender exclusions (optional)

---

### Missing DLL Errors
**Cause**: Incomplete extraction or corrupted download  
**Solution**:
1. Re-download the ZIP/installer
2. Extract to a new folder
3. Disable antivirus temporarily during extraction

---

## 🔐 Security Considerations

### Antivirus False Positives
**Issue**: Some antivirus software may flag PyInstaller executables as suspicious

**Why**: PyInstaller bundles Python runtime, which some AV heuristics flag

**Solutions**:
1. **Code Signing**: Purchase certificate and sign the executable
2. **Submit to AV vendors**: Upload to VirusTotal, report false positive
3. **Whitelist**: Add to antivirus exclusions
4. **Build from source**: Users can build themselves if concerned

---

### Digital Signature (Optional)
**To sign the executable:**

1. **Purchase code signing certificate** (~$100-300/year)
   - Providers: DigiCert, Sectigo, GlobalSign

2. **Sign the EXE**:
   ```powershell
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\OMR_Scanner\OMR_Scanner.exe
   ```

3. **Benefits**:
   - No "Windows protected your PC" warning
   - Shows your organization name
   - Builds user trust
   - Required for some enterprise deployments

---

## 📊 File Size Breakdown

| Component | Size | Purpose |
|-----------|------|---------|
| Python runtime | ~15 MB | Core Python interpreter |
| OpenCV | ~40 MB | Image processing |
| NumPy/Pandas | ~30 MB | Data analysis |
| Plotly | ~20 MB | Interactive charts |
| CustomTkinter | ~5 MB | Modern UI |
| ReportLab | ~10 MB | PDF generation |
| Other libraries | ~30 MB | Various dependencies |
| App code | ~5 MB | Your application |
| Assets | ~2 MB | Images, templates |
| **Total** | **~180 MB** | Uncompressed |
| **ZIP** | **~104 MB** | Compressed |
| **Installer** | **~60-80 MB** | Compressed + installer |

---

## 🔄 Updating the Application

### For Portable Version
1. Build new version
2. Rename ZIP with new version number
3. Users extract to new folder or overwrite old files
4. Database (`data/omr.db`) is preserved

### For Installer Version
1. Update version in `installer.iss`:
   ```ini
   #define AppVersion   "1.1.0"
   ```
2. Rebuild installer
3. Users run new installer (automatically uninstalls old version)

---

## 📦 Customization Before Distribution

### 1. Change App Icon
1. Create/obtain `.ico` file (256x256 recommended)
2. Save as `assets/icon.ico`
3. Uncomment in `build.spec`:
   ```python
   icon="assets/icon.ico",
   ```
4. Uncomment in `installer.iss`:
   ```ini
   SetupIconFile=assets\icon.ico
   ```
5. Rebuild

---

### 2. Update Version Number
**In `installer.iss`**:
```ini
#define AppVersion   "1.0.0"  → "1.1.0"
```

**In `create_portable_zip.ps1`**:
```powershell
$Version = "1.0.0"  → "1.1.0"
```

---

### 3. Change Organization Name
**In `installer.iss`**:
```ini
#define AppPublisher "Your Organization"  → "Afghan MoHE"
#define AppURL       "https://your-org.example.com"  → "https://mohe.gov.af"
```

---

### 4. Regenerate App GUID
**In `installer.iss`**:
1. Open in Inno Setup IDE
2. Tools → Generate GUID
3. Replace existing GUID:
   ```ini
   AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
   ```

---

## 🎯 Recommended Distribution Strategy

### For Afghan MoHE QA Scanner

**Phase 1: Pilot Testing (Portable ZIP)**
- Distribute portable ZIP to 5-10 pilot users
- Collect feedback
- Fix any issues
- No installation hassles

**Phase 2: Department Rollout (Installer)**
- Create signed installer (if budget allows)
- Deploy to all departments
- Provide training
- IT support available

**Phase 3: Maintenance**
- Release updates as portable ZIP for quick fixes
- Release installer for major versions
- Maintain both options

---

## 📞 Support Information

### For Users
**Installation Issues:**
- Check system requirements
- Disable antivirus temporarily
- Run as administrator
- Contact IT support

**Usage Issues:**
- Check user manual
- Watch tutorial videos
- Contact support team

### For IT Administrators
**Deployment:**
- Use Group Policy for installer
- Place portable version on network share
- Create deployment documentation

**Troubleshooting:**
- Check Windows Event Viewer
- Review application logs
- Test on clean VM

---

## ✅ Pre-Distribution Checklist

Before distributing to users:

- [ ] Test on clean Windows 10 VM (no Python installed)
- [ ] Test on clean Windows 11 VM
- [ ] Verify all features work (scan, process, reports)
- [ ] Check database creation and writing
- [ ] Test PDF generation
- [ ] Verify report generation
- [ ] Test with real scanned forms
- [ ] Check for any error messages
- [ ] Verify file paths work correctly
- [ ] Test uninstall (for installer version)
- [ ] Create user documentation
- [ ] Create quick start guide
- [ ] Prepare training materials
- [ ] Set up support channel

---

## 🎉 You're Ready to Deploy!

**Current Status:**
- ✅ Executable built: `dist\OMR_Scanner\OMR_Scanner.exe`
- ✅ Portable ZIP created: `portable_output\OMR_Scanner_Portable_v1.0.0.zip`
- ⚠️ Installer: Requires Inno Setup (optional)

**Next Steps:**
1. Test the portable ZIP on a clean machine
2. If satisfied, distribute to users
3. Optionally install Inno Setup and create installer
4. Collect user feedback
5. Iterate and improve

---

**Version**: 1.0  
**Build Date**: 2026-05-06  
**Build Status**: ✅ Ready for Distribution  
**Distribution Format**: Portable ZIP (104 MB)
