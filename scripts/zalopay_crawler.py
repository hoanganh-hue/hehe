#!/usr/bin/env python3
"""
ZaloPay Website Crawler
Crawls mc.zalopay.vn to extract styles, layouts, and assets for UI cloning
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import urljoin, urlparse

try:
    from playwright.sync_api import sync_playwright, Page
except ImportError:
    print("Error: playwright not installed. Install with: pip install playwright && playwright install")
    sys.exit(1)

# Output directory for crawled data
OUTPUT_DIR = Path(__file__).parent.parent / "frontend" / "zalopay_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Base URL to crawl
BASE_URL = "https://mc.zalopay.vn"

# Pages to crawl
PAGES_TO_CRAWL = [
    "/",
    "/register",
    "/contact",
    "/faq",
    "/solutions",
    "/guide",
]

class ZaloPayCrawler:
    """Crawler for extracting ZaloPay design system and assets"""
    
    def __init__(self):
        self.results = {
            "pages": {},
            "colors": set(),
            "fonts": set(),
            "spacing": set(),
            "images": set(),
            "icons": set(),
            "breakpoints": {},
        }
        
    def extract_computed_styles(self, page: Page, selector: str) -> Dict[str, Any]:
        """Extract computed styles for a given selector"""
        try:
            styles = page.evaluate(f"""
                () => {{
                    const element = document.querySelector('{selector}');
                    if (!element) return null;
                    
                    const computed = window.getComputedStyle(element);
                    return {{
                        color: computed.color,
                        backgroundColor: computed.backgroundColor,
                        fontSize: computed.fontSize,
                        fontFamily: computed.fontFamily,
                        fontWeight: computed.fontWeight,
                        lineHeight: computed.lineHeight,
                        padding: computed.padding,
                        margin: computed.margin,
                        borderRadius: computed.borderRadius,
                        boxShadow: computed.boxShadow,
                        display: computed.display,
                        width: computed.width,
                        height: computed.height,
                    }};
                }}
            """)
            return styles or {}
        except Exception as e:
            print(f"Error extracting styles for {selector}: {e}")
            return {}
    
    def extract_all_colors(self, page: Page) -> List[str]:
        """Extract all unique colors used on the page"""
        try:
            colors = page.evaluate("""
                () => {
                    const colors = new Set();
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(el => {
                        const computed = window.getComputedStyle(el);
                        if (computed.color) colors.add(computed.color);
                        if (computed.backgroundColor) colors.add(computed.backgroundColor);
                        if (computed.borderColor) colors.add(computed.borderColor);
                    });
                    
                    return Array.from(colors);
                }
            """)
            return [c for c in colors if c not in ['rgba(0, 0, 0, 0)', 'transparent']]
        except Exception as e:
            print(f"Error extracting colors: {e}")
            return []
    
    def extract_fonts(self, page: Page) -> List[str]:
        """Extract all font families used on the page"""
        try:
            fonts = page.evaluate("""
                () => {
                    const fonts = new Set();
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(el => {
                        const computed = window.getComputedStyle(el);
                        if (computed.fontFamily) fonts.add(computed.fontFamily);
                    });
                    
                    return Array.from(fonts);
                }
            """)
            return fonts
        except Exception as e:
            print(f"Error extracting fonts: {e}")
            return []
    
    def extract_spacing_values(self, page: Page) -> List[str]:
        """Extract unique spacing values (padding, margin)"""
        try:
            spacing = page.evaluate("""
                () => {
                    const spacing = new Set();
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(el => {
                        const computed = window.getComputedStyle(el);
                        if (computed.padding && computed.padding !== '0px') spacing.add(computed.padding);
                        if (computed.margin && computed.margin !== '0px') spacing.add(computed.margin);
                        if (computed.paddingTop && computed.paddingTop !== '0px') spacing.add(computed.paddingTop);
                        if (computed.paddingBottom && computed.paddingBottom !== '0px') spacing.add(computed.paddingBottom);
                        if (computed.marginTop && computed.marginTop !== '0px') spacing.add(computed.marginTop);
                        if (computed.marginBottom && computed.marginBottom !== '0px') spacing.add(computed.marginBottom);
                    });
                    
                    return Array.from(spacing);
                }
            """)
            return spacing
        except Exception as e:
            print(f"Error extracting spacing: {e}")
            return []
    
    def extract_assets(self, page: Page) -> Dict[str, List[str]]:
        """Extract all image and icon URLs"""
        try:
            assets = page.evaluate("""
                () => {
                    const images = new Set();
                    const icons = new Set();
                    
                    // Extract images
                    document.querySelectorAll('img').forEach(img => {
                        if (img.src) images.add(img.src);
                    });
                    
                    // Extract background images
                    document.querySelectorAll('*').forEach(el => {
                        const computed = window.getComputedStyle(el);
                        const bgImage = computed.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            const matches = bgImage.match(/url\\(["']?([^"')]+)["']?\\)/g);
                            if (matches) {
                                matches.forEach(match => {
                                    const url = match.replace(/url\\(["']?/, '').replace(/["']?\\)/, '');
                                    if (url.endsWith('.svg')) {
                                        icons.add(url);
                                    } else {
                                        images.add(url);
                                    }
                                });
                            }
                        }
                    });
                    
                    // Extract SVG icons
                    document.querySelectorAll('svg').forEach(svg => {
                        icons.add('inline-svg');
                    });
                    
                    return {
                        images: Array.from(images),
                        icons: Array.from(icons)
                    };
                }
            """)
            return assets
        except Exception as e:
            print(f"Error extracting assets: {e}")
            return {"images": [], "icons": []}
    
    def extract_layout_structure(self, page: Page) -> Dict[str, Any]:
        """Extract page layout structure"""
        try:
            layout = page.evaluate("""
                () => {
                    const structure = {
                        header: null,
                        navigation: null,
                        main: null,
                        footer: null,
                        sections: []
                    };
                    
                    // Extract header
                    const header = document.querySelector('header, .header, nav');
                    if (header) {
                        structure.header = {
                            tag: header.tagName,
                            classes: Array.from(header.classList)
                        };
                    }
                    
                    // Extract main sections
                    const sections = document.querySelectorAll('section, .section, main > div');
                    sections.forEach(section => {
                        structure.sections.push({
                            tag: section.tagName,
                            classes: Array.from(section.classList),
                            id: section.id || null
                        });
                    });
                    
                    // Extract footer
                    const footer = document.querySelector('footer, .footer');
                    if (footer) {
                        structure.footer = {
                            tag: footer.tagName,
                            classes: Array.from(footer.classList)
                        };
                    }
                    
                    return structure;
                }
            """)
            return layout
        except Exception as e:
            print(f"Error extracting layout: {e}")
            return {}
    
    def crawl_page(self, page: Page, url: str) -> Dict[str, Any]:
        """Crawl a single page and extract all relevant information"""
        print(f"Crawling: {url}")
        
        try:
            # Navigate to page
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Take screenshots
            screenshot_dir = OUTPUT_DIR / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            
            page_name = urlparse(url).path.strip('/').replace('/', '_') or 'index'
            page.screenshot(path=str(screenshot_dir / f"{page_name}_full.png"), full_page=True)
            page.screenshot(path=str(screenshot_dir / f"{page_name}_viewport.png"))
            
            # Extract data
            page_data = {
                "url": url,
                "title": page.title(),
                "colors": self.extract_all_colors(page),
                "fonts": self.extract_fonts(page),
                "spacing": self.extract_spacing_values(page),
                "assets": self.extract_assets(page),
                "layout": self.extract_layout_structure(page),
                "viewport": page.viewport_size,
            }
            
            # Extract specific component styles
            components = {
                "header": self.extract_computed_styles(page, "header, .header, nav"),
                "button": self.extract_computed_styles(page, "button, .btn, .button"),
                "card": self.extract_computed_styles(page, ".card, .card-container"),
                "form": self.extract_computed_styles(page, "form, .form"),
                "footer": self.extract_computed_styles(page, "footer, .footer"),
            }
            page_data["components"] = components
            
            # Update global results
            self.results["colors"].update(page_data["colors"])
            self.results["fonts"].update(page_data["fonts"])
            self.results["spacing"].update(page_data["spacing"])
            self.results["images"].update(page_data["assets"]["images"])
            self.results["icons"].update(page_data["assets"]["icons"])
            
            return page_data
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return {"url": url, "error": str(e)}
    
    def crawl(self):
        """Main crawling method"""
        print("Starting ZaloPay crawler...")
        print(f"Output directory: {OUTPUT_DIR}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            # Crawl each page
            for path in PAGES_TO_CRAWL:
                url = urljoin(BASE_URL, path)
                page_data = self.crawl_page(page, url)
                
                page_name = path.strip('/').replace('/', '_') or 'index'
                self.results["pages"][page_name] = page_data
                
                # Save individual page data
                page_file = OUTPUT_DIR / f"page_{page_name}.json"
                with open(page_file, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=2, ensure_ascii=False)
                print(f"  Saved: {page_file}")
            
            browser.close()
        
        # Convert sets to lists for JSON serialization
        self.results["colors"] = sorted(list(self.results["colors"]))
        self.results["fonts"] = sorted(list(self.results["fonts"]))
        self.results["spacing"] = sorted(list(self.results["spacing"]))
        self.results["images"] = sorted(list(self.results["images"]))
        self.results["icons"] = sorted(list(self.results["icons"]))
        
        # Save combined results
        results_file = OUTPUT_DIR / "crawl_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\nCrawl complete! Results saved to: {results_file}")
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print crawl summary"""
        print("\n" + "="*60)
        print("CRAWL SUMMARY")
        print("="*60)
        print(f"Pages crawled: {len(self.results['pages'])}")
        print(f"Unique colors: {len(self.results['colors'])}")
        print(f"Font families: {len(self.results['fonts'])}")
        print(f"Spacing values: {len(self.results['spacing'])}")
        print(f"Images found: {len(self.results['images'])}")
        print(f"Icons found: {len(self.results['icons'])}")
        print("="*60)
        
        print("\nTop 10 Colors:")
        for color in self.results['colors'][:10]:
            print(f"  - {color}")
        
        print("\nFont Families:")
        for font in self.results['fonts']:
            print(f"  - {font}")


def main():
    """Main entry point"""
    crawler = ZaloPayCrawler()
    crawler.crawl()


if __name__ == "__main__":
    main()
