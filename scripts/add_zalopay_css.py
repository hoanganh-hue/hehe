#!/usr/bin/env python3
"""
Script to automatically add ZaloPay CSS imports to all HTML files
"""

import os
import re
from pathlib import Path

# Directories
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
MERCHANT_DIR = FRONTEND_DIR / "merchant"
ADMIN_DIR = FRONTEND_DIR / "admin"

# CSS imports to add (for merchant pages)
MERCHANT_CSS_IMPORTS = '''    <!-- ZaloPay Design System -->
    <link href="/css/zalopay-variables.css" rel="stylesheet">
    <link href="/css/zalopay-shared.css" rel="stylesheet">
    <link href="/css/zalopay-components.css" rel="stylesheet">
    '''

# CSS imports to add (for admin pages)
ADMIN_CSS_IMPORTS = '''    <!-- ZaloPay Design System -->
    <link href="/css/zalopay-variables.css" rel="stylesheet">
    <link href="/css/zalopay-shared.css" rel="stylesheet">
    <link href="/css/zalopay-components.css" rel="stylesheet">
    <link href="/admin/css/zalopay-admin.css" rel="stylesheet">
    '''


def has_zalopay_css(content: str) -> bool:
    """Check if ZaloPay CSS is already imported"""
    return 'zalopay-variables.css' in content


def add_css_imports(file_path: Path, css_imports: str):
    """Add ZaloPay CSS imports to an HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has ZaloPay CSS
        if has_zalopay_css(content):
            print(f"  ⏭️  Skipped (already has ZaloPay CSS): {file_path.name}")
            return False
        
        # Find the position to insert (after Bootstrap CSS or before first stylesheet)
        # Look for Bootstrap CSS link
        bootstrap_pattern = r'(<link[^>]*bootstrap[^>]*>)'
        match = re.search(bootstrap_pattern, content, re.IGNORECASE)
        
        if match:
            # Insert after Bootstrap
            insert_pos = match.end()
            new_content = content[:insert_pos] + '\n' + css_imports + content[insert_pos:]
        else:
            # Try to find first CSS link
            css_pattern = r'(<link[^>]*rel="stylesheet"[^>]*>)'
            match = re.search(css_pattern, content, re.IGNORECASE)
            
            if match:
                # Insert before first CSS
                insert_pos = match.start()
                new_content = content[:insert_pos] + css_imports + '\n    ' + content[insert_pos:]
            else:
                # Try to find </head>
                head_pattern = r'(</head>)'
                match = re.search(head_pattern, content, re.IGNORECASE)
                
                if match:
                    # Insert before </head>
                    insert_pos = match.start()
                    new_content = content[:insert_pos] + css_imports + '\n    ' + content[insert_pos:]
                else:
                    print(f"  ❌ Could not find insertion point in: {file_path.name}")
                    return False
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ Updated: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing {file_path.name}: {e}")
        return False


def process_directory(directory: Path, css_imports: str, label: str):
    """Process all HTML files in a directory"""
    print(f"\n{label}")
    print("="*60)
    
    updated_count = 0
    skipped_count = 0
    
    html_files = sorted(directory.glob("*.html"))
    
    for html_file in html_files:
        if add_css_imports(html_file, css_imports):
            updated_count += 1
        else:
            skipped_count += 1
    
    print(f"\nSummary for {label}:")
    print(f"  Updated: {updated_count} files")
    print(f"  Skipped: {skipped_count} files")
    
    return updated_count, skipped_count


def main():
    """Main entry point"""
    print("ZaloPay CSS Import Tool")
    print("="*60)
    print("This script adds ZaloPay CSS imports to all HTML files")
    print()
    
    total_updated = 0
    total_skipped = 0
    
    # Process merchant pages
    if MERCHANT_DIR.exists():
        updated, skipped = process_directory(
            MERCHANT_DIR,
            MERCHANT_CSS_IMPORTS,
            "📄 Processing Merchant Pages"
        )
        total_updated += updated
        total_skipped += skipped
    
    # Process admin pages
    if ADMIN_DIR.exists():
        updated, skipped = process_directory(
            ADMIN_DIR,
            ADMIN_CSS_IMPORTS,
            "📄 Processing Admin Pages"
        )
        total_updated += updated
        total_skipped += skipped
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total files updated: {total_updated}")
    print(f"Total files skipped: {total_skipped}")
    print(f"Total files processed: {total_updated + total_skipped}")
    print("="*60)
    print("\n✨ Done!")


if __name__ == "__main__":
    main()
