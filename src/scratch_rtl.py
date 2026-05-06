import os
from pathlib import Path

pages_dir = Path('d:/Projects/OMR/src/pages')

for f in pages_dir.glob('*.py'):
    content = f.read_text('utf-8')
    needs_update = False
    
    if 'get_start' not in content and ('side="left"' in content or 'side="right"' in content or 'anchor="w"' in content or 'compound="left"' in content):
        if 'from i18n import _\n' in content:
            content = content.replace('from i18n import _\n', 'from i18n import _, get_start, get_end, get_anchor, get_compound\n')
        elif 'from i18n import _, is_rtl\n' in content:
            content = content.replace('from i18n import _, is_rtl\n', 'from i18n import _, is_rtl, get_start, get_end, get_anchor, get_compound\n')
        elif 'from i18n import I18n, _\n' in content:
            content = content.replace('from i18n import I18n, _\n', 'from i18n import I18n, _, get_start, get_end, get_anchor, get_compound\n')
        elif 'from i18n import _, is_rtl, I18n\n' in content:
            content = content.replace('from i18n import _, is_rtl, I18n\n', 'from i18n import _, is_rtl, I18n, get_start, get_end, get_anchor, get_compound\n')
        needs_update = True
        
    if 'side="left"' in content:
        content = content.replace('side="left"', 'side=get_start()')
        needs_update = True
    if 'side="right"' in content:
        content = content.replace('side="right"', 'side=get_end()')
        needs_update = True
    if 'anchor="w"' in content:
        content = content.replace('anchor="w"', 'anchor=get_anchor()')
        needs_update = True
    if 'compound="left"' in content:
        content = content.replace('compound="left"', 'compound=get_compound()')
        needs_update = True
        
    if needs_update:
        f.write_text(content, 'utf-8')
        print(f"Updated {f.name}")
print("Done!")
