# Permission Denied Fix - Report Generation

## Issue

**Error Message:**
```
Failed to generate report:
[Errno 13] Permission denied: 'C:\Program Files\Tadris QA System\_internal\assets\dari_qa_report.html'
```

**Root Cause:**
The application was trying to write HTML reports to the `Program Files` directory, which requires administrator privileges on Windows. This is a common issue with applications installed in protected system directories.

## Solution

Reports are now saved to a writable user directory:

### Production (Installed App)
```
C:\Users\<username>\Documents\Tadris_QA\Reports\
```

### Development
```
<project_root>\assets\
```

## Changes Made

### 1. `src/config.py`
Added a new method to get the writable reports directory:

```python
@staticmethod
def get_reports_dir() -> Path:
    """Get the directory for generated reports (writable location).
    
    In production (PyInstaller bundle), uses user's Documents folder.
    In development, uses project's assets folder.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - use Documents folder
        if sys.platform == 'win32':
            import os
            documents = Path(os.path.expanduser("~")) / "Documents" / "Tadris_QA" / "Reports"
        else:
            documents = Path.home() / "Tadris_QA" / "Reports"
        
        # Create directory if it doesn't exist
        documents.mkdir(parents=True, exist_ok=True)
        return documents
    else:
        # Development mode - use assets folder (writable)
        return Config.ASSETS_DIR
```

### 2. `src/pages/results.py`
Updated to use the writable reports directory:

```python
# Before
report_path = str(Config.PROJECT_ROOT / "assets" / "dari_qa_report.html")

# After
reports_dir = Config.get_reports_dir()
report_path = str(reports_dir / "dari_qa_report.html")
```

### 3. `src/pages/dashboard.py`
Same update as results.py:

```python
# Before
report_path = str(Config.PROJECT_ROOT / "assets" / "dari_qa_report.html")

# After
reports_dir = Config.get_reports_dir()
report_path = str(reports_dir / "dari_qa_report.html")
```

## Benefits

1. **No Permission Errors**: Reports are saved to user's Documents folder (always writable)
2. **User-Friendly**: Reports are in a familiar location (Documents folder)
3. **Easy Access**: Users can easily find and share their reports
4. **Automatic Directory Creation**: The directory is created automatically if it doesn't exist
5. **Cross-Platform**: Works on Windows, Linux, and macOS

## Report Locations

### Windows
```
C:\Users\<username>\Documents\Tadris_QA\Reports\dari_qa_report.html
```

### Linux/macOS
```
~/Tadris_QA/Reports/dari_qa_report.html
```

## User Experience

When users generate a report:
1. Report is saved to `Documents\Tadris_QA\Reports\`
2. Report opens automatically in the default browser
3. Users can find all their reports in one location
4. No permission errors or admin prompts

## Testing

Run the test to verify:
```powershell
.\venv\Scripts\python.exe test_writable_reports.py
```

Expected output:
```
✅ Reports directory is writable
✅ Report generation to writable location works
✅ Frozen mode simulation passed

Reports will be saved to:
  Development: D:\Projects\OMR\assets
  Production:  C:\Users\<username>\Documents\Tadris_QA\Reports
```

## Migration Notes

### For Existing Users
- Old reports in `Program Files` (if any) will remain there
- New reports will be saved to `Documents\Tadris_QA\Reports\`
- Users can manually copy old reports if needed

### For Developers
- Development mode unchanged (still uses `assets/` folder)
- Production mode automatically uses Documents folder
- No configuration needed

## Troubleshooting

### Issue: Reports still not saving
**Check:**
1. Verify Documents folder exists and is writable
2. Check disk space
3. Check antivirus/security software

### Issue: Can't find reports
**Location:**
- Windows: `C:\Users\<username>\Documents\Tadris_QA\Reports\`
- Open File Explorer → Documents → Tadris_QA → Reports

### Issue: Want to change report location
**Solution:**
Edit `Config.get_reports_dir()` in `src/config.py` to use a different directory.

## Related Issues

This fix also applies to:
- Any other file output operations
- Export functionality
- Backup files
- Log files (if needed in the future)

## Best Practices

For future file operations:
1. ✅ Use `Config.get_reports_dir()` for user-generated content
2. ✅ Use AppData for application data (database, settings)
3. ✅ Never write to Program Files
4. ✅ Always create directories with `mkdir(parents=True, exist_ok=True)`
5. ✅ Handle permission errors gracefully

## Summary

The permission denied error has been fixed by:
- Moving report output to user's Documents folder
- Automatically creating the directory if needed
- Maintaining backward compatibility with development mode
- Providing a user-friendly location for reports

Users will no longer see permission errors when generating reports! ✅
