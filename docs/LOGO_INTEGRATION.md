# Logo Integration Guide

This document describes how the Tadris QA System logo has been integrated into the application.

## Logo Files

### Source Logo
- **File**: `assets/app logo.png`
- **Format**: PNG (1254x1254 pixels)
- **Usage**: Displayed in the GUI sidebar

### Application Icon
- **File**: `assets/app_icon.ico`
- **Format**: ICO with multiple sizes (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
- **Usage**: Windows executable icon and installer icon

## Integration Points

### 1. GUI Sidebar (src/app.py)
The logo is displayed at the top of the sidebar:
- Size: 80x80 pixels
- Position: Centered above the "Tadris QA" text
- Fallback: If logo fails to load, only text is shown

### 2. Windows Executable (build.spec)
The icon is embedded in the compiled executable:
```python
icon="assets/app_icon.ico"
```

### 3. Installer (installer.iss)
The icon is used for:
- Setup installer icon
- Installed application icon
- Uninstall program icon

```ini
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
```

## Updating the Logo

If you need to change the application logo:

### Step 1: Replace the PNG
Replace `assets/app logo.png` with your new logo:
- Recommended: Square image (1:1 aspect ratio)
- Format: PNG with transparency support
- Minimum size: 256x256 pixels
- Recommended size: 512x512 or larger

### Step 2: Convert to ICO
Run the conversion script:
```powershell
python convert_logo_to_ico.py
```

This will:
- Load `assets/app logo.png`
- Create a square canvas if needed
- Generate `assets/app_icon.ico` with multiple sizes
- Preserve transparency

### Step 3: Rebuild the Application
```powershell
.\build_installer.ps1
```

The new logo will be:
- Displayed in the GUI sidebar
- Embedded in the executable
- Shown in the installer

## Technical Details

### Logo Display in GUI
- Uses PIL/Pillow for image loading
- Resized to 80x80 pixels using LANCZOS resampling
- Wrapped in CTkImage for CustomTkinter compatibility
- Centered in the sidebar with 12px bottom padding

### Icon Conversion
- Converts PNG to ICO format
- Creates multiple sizes for different display contexts
- Maintains transparency (RGBA mode)
- Centers non-square images on transparent background

### Build Integration
- Icon is bundled with PyInstaller
- Embedded in the executable at compile time
- Used by Windows for taskbar, alt-tab, and file explorer

## Troubleshooting

### Logo not showing in GUI
1. Check that `assets/app logo.png` exists
2. Verify PIL/Pillow is installed: `pip install pillow`
3. Check console for warning messages
4. Ensure the image file is not corrupted

### Icon not showing in executable
1. Verify `assets/app_icon.ico` exists
2. Check that build.spec has the correct icon path
3. Rebuild the application: `pyinstaller build.spec --noconfirm`
4. Clear the build cache: `Remove-Item -Recurse build, dist`

### Icon not showing in installer
1. Verify `assets/app_icon.ico` exists
2. Check that installer.iss has the correct icon path
3. Rebuild the installer: `iscc installer.iss`

## File Locations

```
assets/
├── app logo.png          # Source logo (PNG)
└── app_icon.ico          # Windows icon (ICO)

src/
└── app.py                # GUI logo display

build.spec                # Executable icon configuration
installer.iss             # Installer icon configuration
convert_logo_to_ico.py    # Logo conversion utility
```

## Notes

- The logo is loaded at runtime in the GUI, so changes to `app logo.png` are visible immediately during development
- The icon is embedded at build time, so changes to `app_icon.ico` require rebuilding the executable
- The conversion script preserves transparency and handles non-square images automatically
- Multiple icon sizes ensure optimal display at different resolutions and contexts
