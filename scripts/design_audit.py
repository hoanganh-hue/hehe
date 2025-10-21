#!/usr/bin/env python3
"""
ZaloPay Design Audit Script
Automated checker for design consistency across all pages
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

# Directories
SCRIPT_DIR = Path(__file__).parent
FRONTEND_DIR = SCRIPT_DIR.parent / "frontend"
OUTPUT_DIR = FRONTEND_DIR / "zalopay_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Expected ZaloPay colors
EXPECTED_COLORS = {
    '#0068FF', '#0052CC', '#3D8AFF', '#E5F0FF',  # Blues
    '#00C896', '#00A078', '#33D4A9',              # Greens
    '#FF6D3D', '#7B61FF', '#FFB800',              # Accents
}

# Expected fonts
EXPECTED_FONTS = {
    'SF Pro Display',
    'Inter',
    'Roboto',
    'Arial',
    'sans-serif',
}

# Expected spacing values (in rem or px)
EXPECTED_SPACING = {
    '0.25rem', '0.5rem', '0.75rem', '1rem', '1.25rem', '1.5rem',
    '2rem', '2.5rem', '3rem', '4rem', '5rem', '6rem', '8rem',
    '4px', '8px', '12px', '16px', '20px', '24px', '32px', '40px', '48px', '64px',
}


class DesignAuditor:
    """Audits HTML and CSS files for design consistency"""
    
    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = {
            "files_checked": 0,
            "total_issues": 0,
            "colors_found": set(),
            "fonts_found": set(),
            "spacing_found": set(),
        }
    
    def audit_html_file(self, file_path: Path):
        """Audit a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.stats["files_checked"] += 1
            
            # Check for inline styles (should be avoided)
            inline_styles = re.findall(r'style="([^"]*)"', content)
            if inline_styles:
                self.issues[str(file_path)].append({
                    "type": "inline_style",
                    "severity": "warning",
                    "message": f"Found {len(inline_styles)} inline styles (should use CSS classes)",
                    "count": len(inline_styles)
                })
            
            # Check for old color references
            old_colors = re.findall(r'#[0-9A-Fa-f]{6}', content)
            for color in old_colors:
                if color.upper() not in EXPECTED_COLORS:
                    self.issues[str(file_path)].append({
                        "type": "unexpected_color",
                        "severity": "info",
                        "message": f"Unexpected color found: {color}",
                        "value": color
                    })
            
            # Check if ZaloPay CSS is imported
            has_zalopay_css = (
                'zalopay-variables.css' in content or
                'zalopay-components.css' in content or
                'zalopay-shared.css' in content
            )
            
            if not has_zalopay_css:
                self.issues[str(file_path)].append({
                    "type": "missing_zalopay_css",
                    "severity": "error",
                    "message": "ZaloPay CSS files not imported"
                })
            
            # Check for accessibility attributes
            has_alt_text = 'alt=' in content or 'alt =' in content
            img_count = content.count('<img')
            
            if img_count > 0 and not has_alt_text:
                self.issues[str(file_path)].append({
                    "type": "accessibility",
                    "severity": "warning",
                    "message": "Images without alt text"
                })
            
        except Exception as e:
            self.issues[str(file_path)].append({
                "type": "error",
                "severity": "error",
                "message": f"Failed to audit file: {str(e)}"
            })
    
    def audit_css_file(self, file_path: Path):
        """Audit a single CSS file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.stats["files_checked"] += 1
            
            # Extract colors
            colors = re.findall(r'#[0-9A-Fa-f]{6}', content)
            rgb_colors = re.findall(r'rgb\([^)]+\)', content)
            rgba_colors = re.findall(r'rgba\([^)]+\)', content)
            
            self.stats["colors_found"].update(colors)
            
            # Check for hardcoded colors (should use CSS variables)
            if colors or rgb_colors or rgba_colors:
                hardcoded_count = len(colors) + len(rgb_colors) + len(rgba_colors)
                
                # Check if these are definitions (in :root) vs usage
                is_variable_definition = ':root' in content[:1000]
                
                if not is_variable_definition and hardcoded_count > 5:
                    self.issues[str(file_path)].append({
                        "type": "hardcoded_colors",
                        "severity": "warning",
                        "message": f"Found {hardcoded_count} hardcoded colors (should use CSS variables)",
                        "count": hardcoded_count
                    })
            
            # Extract font families
            fonts = re.findall(r'font-family:\s*([^;]+);', content)
            for font in fonts:
                font_clean = font.strip().strip("'\"")
                self.stats["fonts_found"].add(font_clean)
            
            # Extract spacing values
            spacing = re.findall(r'(?:padding|margin):\s*([^;]+);', content)
            for space in spacing:
                self.stats["spacing_found"].add(space.strip())
            
            # Check for !important (should be avoided)
            important_count = content.count('!important')
            if important_count > 10:
                self.issues[str(file_path)].append({
                    "type": "important_overuse",
                    "severity": "warning",
                    "message": f"Excessive use of !important ({important_count} times)",
                    "count": important_count
                })
            
        except Exception as e:
            self.issues[str(file_path)].append({
                "type": "error",
                "severity": "error",
                "message": f"Failed to audit file: {str(e)}"
            })
    
    def audit_all_files(self):
        """Audit all HTML and CSS files"""
        print("🔍 Starting Design Audit...")
        print("="*60)
        
        # Audit merchant HTML files
        merchant_dir = FRONTEND_DIR / "merchant"
        if merchant_dir.exists():
            print(f"\n📄 Auditing Merchant Pages...")
            for html_file in merchant_dir.glob("*.html"):
                self.audit_html_file(html_file)
                print(f"  ✓ {html_file.name}")
        
        # Audit admin HTML files
        admin_dir = FRONTEND_DIR / "admin"
        if admin_dir.exists():
            print(f"\n📄 Auditing Admin Pages...")
            for html_file in admin_dir.glob("*.html"):
                self.audit_html_file(html_file)
                print(f"  ✓ {html_file.name}")
        
        # Audit CSS files
        css_dir = FRONTEND_DIR / "css"
        if css_dir.exists():
            print(f"\n🎨 Auditing CSS Files...")
            for css_file in css_dir.glob("*.css"):
                self.audit_css_file(css_file)
                print(f"  ✓ {css_file.name}")
        
        # Count total issues
        for file_issues in self.issues.values():
            self.stats["total_issues"] += len(file_issues)
    
    def generate_report(self):
        """Generate audit report"""
        report = {
            "summary": {
                "files_checked": self.stats["files_checked"],
                "total_issues": self.stats["total_issues"],
                "colors_found": len(self.stats["colors_found"]),
                "fonts_found": len(self.stats["fonts_found"]),
                "spacing_values": len(self.stats["spacing_found"]),
            },
            "issues": dict(self.issues),
            "design_tokens": {
                "colors": sorted(list(self.stats["colors_found"])),
                "fonts": sorted(list(self.stats["fonts_found"])),
                "spacing": sorted(list(self.stats["spacing_found"]))[:20],  # Top 20
            }
        }
        
        # Save report
        report_file = OUTPUT_DIR / "design_audit_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Report saved: {report_file}")
        return report
    
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        print(f"Files checked: {self.stats['files_checked']}")
        print(f"Total issues: {self.stats['total_issues']}")
        print(f"Unique colors: {len(self.stats['colors_found'])}")
        print(f"Font families: {len(self.stats['fonts_found'])}")
        print(f"Spacing values: {len(self.stats['spacing_found'])}")
        print("="*60)
        
        # Count by severity
        severity_counts = defaultdict(int)
        for file_issues in self.issues.values():
            for issue in file_issues:
                severity_counts[issue.get('severity', 'unknown')] += 1
        
        if severity_counts:
            print("\nIssues by Severity:")
            for severity, count in sorted(severity_counts.items()):
                icon = "🔴" if severity == "error" else "⚠️" if severity == "warning" else "ℹ️"
                print(f"  {icon} {severity.upper()}: {count}")
        
        # Top issues
        if self.issues:
            print("\nTop Issues:")
            issue_types = defaultdict(int)
            for file_issues in self.issues.values():
                for issue in file_issues:
                    issue_types[issue['type']] += 1
            
            for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {issue_type}: {count} occurrences")
        
        print("\n💡 Recommendations:")
        print("  1. Use CSS variables for colors instead of hardcoded values")
        print("  2. Import ZaloPay CSS files in all pages")
        print("  3. Avoid inline styles - use utility classes")
        print("  4. Minimize use of !important declarations")
        print("  5. Ensure all images have alt text for accessibility")


def main():
    """Main entry point"""
    print("ZaloPay Design Audit Tool")
    print("="*60)
    
    auditor = DesignAuditor()
    auditor.audit_all_files()
    auditor.generate_report()
    auditor.print_summary()
    
    print("\n✨ Audit complete!")


if __name__ == "__main__":
    main()
