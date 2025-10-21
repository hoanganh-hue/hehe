#!/usr/bin/env python3
"""
ZaloPay Assets Downloader
Downloads images, fonts, icons, and SVGs from ZaloPay website
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib
import mimetypes

try:
    import requests
except ImportError:
    print("Error: requests not installed. Install with: pip install requests")
    sys.exit(1)

# Directories
SCRIPT_DIR = Path(__file__).parent
FRONTEND_DIR = SCRIPT_DIR.parent / "frontend"
PUBLIC_DIR = FRONTEND_DIR / "public"
ANALYSIS_DIR = FRONTEND_DIR / "zalopay_analysis"

# Asset directories
IMAGES_DIR = PUBLIC_DIR / "images" / "zalopay"
FONTS_DIR = PUBLIC_DIR / "fonts" / "zalopay"
ICONS_DIR = PUBLIC_DIR / "icons" / "zalopay"

# Create directories
for directory in [IMAGES_DIR, FONTS_DIR, ICONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Base URL
BASE_URL = "https://mc.zalopay.vn"


class AssetDownloader:
    """Downloads and organizes ZaloPay assets"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.downloaded = {
            "images": [],
            "fonts": [],
            "icons": [],
            "errors": []
        }
    
    def get_filename_from_url(self, url: str) -> str:
        """Generate a safe filename from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        # Get filename from path
        filename = os.path.basename(path)
        if not filename:
            # Generate from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            ext = mimetypes.guess_extension(parsed.path) or '.bin'
            filename = f"asset_{url_hash}{ext}"
        
        # Clean filename
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        return filename
    
    def download_file(self, url: str, output_path: Path) -> bool:
        """Download a single file"""
        try:
            # Make absolute URL
            if not url.startswith('http'):
                url = urljoin(BASE_URL, url)
            
            # Skip if already downloaded
            if output_path.exists():
                print(f"  ⏭️  Skipped (exists): {output_path.name}")
                return True
            
            # Download
            print(f"  ⬇️  Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✅ Saved: {output_path.name} ({len(response.content)} bytes)")
            return True
            
        except Exception as e:
            error_msg = f"Failed to download {url}: {e}"
            print(f"  ❌ {error_msg}")
            self.downloaded["errors"].append(error_msg)
            return False
    
    def download_images(self, image_urls: list):
        """Download all images"""
        print(f"\n{'='*60}")
        print("DOWNLOADING IMAGES")
        print(f"{'='*60}")
        print(f"Total images to download: {len(image_urls)}")
        
        for url in image_urls:
            if not url or url == 'inline-svg':
                continue
            
            filename = self.get_filename_from_url(url)
            output_path = IMAGES_DIR / filename
            
            if self.download_file(url, output_path):
                self.downloaded["images"].append(str(output_path.relative_to(FRONTEND_DIR)))
        
        print(f"\n✅ Downloaded {len(self.downloaded['images'])} images")
    
    def download_icons(self, icon_urls: list):
        """Download all icons"""
        print(f"\n{'='*60}")
        print("DOWNLOADING ICONS")
        print(f"{'='*60}")
        print(f"Total icons to download: {len(icon_urls)}")
        
        for url in icon_urls:
            if not url or url == 'inline-svg':
                continue
            
            filename = self.get_filename_from_url(url)
            output_path = ICONS_DIR / filename
            
            if self.download_file(url, output_path):
                self.downloaded["icons"].append(str(output_path.relative_to(FRONTEND_DIR)))
        
        print(f"\n✅ Downloaded {len(self.downloaded['icons'])} icons")
    
    def download_fonts(self):
        """Download common web fonts used by ZaloPay"""
        print(f"\n{'='*60}")
        print("DOWNLOADING FONTS")
        print(f"{'='*60}")
        
        # Common fonts used by ZaloPay (approximation)
        font_urls = [
            # SF Pro Display (Apple's font - using similar alternatives)
            "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
            "https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap",
            "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap",
        ]
        
        for url in font_urls:
            font_name = urlparse(url).query.split('family=')[1].split(':')[0] if 'family=' in url else 'font'
            filename = f"{font_name}.css"
            output_path = FONTS_DIR / filename
            
            if self.download_file(url, output_path):
                self.downloaded["fonts"].append(str(output_path.relative_to(FRONTEND_DIR)))
        
        print(f"\n✅ Downloaded {len(self.downloaded['fonts'])} font files")
    
    def create_asset_manifest(self):
        """Create a manifest file with all downloaded assets"""
        manifest_path = PUBLIC_DIR / "zalopay_assets_manifest.json"
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.downloaded, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Asset manifest created: {manifest_path}")
    
    def download_from_crawl_results(self):
        """Download assets based on crawler results"""
        # Check if crawl results exist
        crawl_results_file = ANALYSIS_DIR / "crawl_results.json"
        
        if not crawl_results_file.exists():
            print(f"⚠️  Crawl results not found at: {crawl_results_file}")
            print("Please run zalopay_crawler.py first!")
            
            # Create sample data for testing
            print("\n📝 Creating sample asset list for testing...")
            sample_images = []
            sample_icons = []
        else:
            print(f"📂 Loading crawl results from: {crawl_results_file}")
            with open(crawl_results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            sample_images = results.get("images", [])
            sample_icons = results.get("icons", [])
        
        # Download images
        if sample_images:
            self.download_images(sample_images)
        else:
            print("\n⚠️  No images found in crawl results")
        
        # Download icons
        if sample_icons:
            self.download_icons(sample_icons)
        else:
            print("\n⚠️  No icons found in crawl results")
        
        # Download fonts
        self.download_fonts()
        
        # Create manifest
        self.create_asset_manifest()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print download summary"""
        print(f"\n{'='*60}")
        print("DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Images downloaded: {len(self.downloaded['images'])}")
        print(f"Icons downloaded: {len(self.downloaded['icons'])}")
        print(f"Fonts downloaded: {len(self.downloaded['fonts'])}")
        print(f"Errors: {len(self.downloaded['errors'])}")
        print(f"{'='*60}")
        
        if self.downloaded['errors']:
            print("\n⚠️  Errors encountered:")
            for error in self.downloaded['errors'][:10]:
                print(f"  - {error}")
            if len(self.downloaded['errors']) > 10:
                print(f"  ... and {len(self.downloaded['errors']) - 10} more")
        
        print("\n📁 Assets saved to:")
        print(f"  Images: {IMAGES_DIR}")
        print(f"  Icons: {ICONS_DIR}")
        print(f"  Fonts: {FONTS_DIR}")


def main():
    """Main entry point"""
    print("ZaloPay Assets Downloader")
    print("="*60)
    
    downloader = AssetDownloader()
    downloader.download_from_crawl_results()
    
    print("\n✨ Download complete!")


if __name__ == "__main__":
    main()
