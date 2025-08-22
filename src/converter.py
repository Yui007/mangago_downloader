"""
Conversion functionality for the Mangago Downloader.
Supports converting downloaded manga images to PDF and CBZ formats.
"""
import os
import zipfile
from pathlib import Path
from typing import List, Optional
import img2pdf
from PIL import Image


def convert_to_pdf(
    chapter_dir: str,
    output_path: Optional[str] = None,
    delete_images: bool = False
) -> Optional[str]:
    """
    Convert chapter images to a high-quality PDF without re-encoding.
    """
    try:
        image_files = _get_image_files(chapter_dir)
        if not image_files:
            print(f"No images found in {chapter_dir}")
            return None
        
        image_files.sort()
        
        if not output_path:
            chapter_name = os.path.basename(chapter_dir)
            output_path = os.path.join(chapter_dir, f"{chapter_name}.pdf")
        
        # By passing the raw image data, img2pdf avoids re-encoding and preserves quality.
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert([open(i, "rb").read() for i in image_files]))
        
        if delete_images:
            for image_file in image_files:
                try:
                    os.remove(image_file)
                except OSError as e:
                    print(f"Warning: Failed to delete {image_file}: {e}")
        
        return output_path
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return None


def convert_to_cbz(
    chapter_dir: str,
    output_path: Optional[str] = None,
    delete_images: bool = False
) -> Optional[str]:
    """
    Convert chapter images to CBZ (Comic Book ZIP).
    """
    try:
        image_files = _get_image_files(chapter_dir)
        if not image_files:
            print(f"No images found in {chapter_dir}")
            return None
        
        image_files.sort()
        
        if not output_path:
            chapter_name = os.path.basename(chapter_dir)
            output_path = os.path.join(chapter_dir, f"{chapter_name}.cbz")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_file in image_files:
                arcname = os.path.basename(image_file)
                zipf.write(image_file, arcname)
        
        if delete_images:
            for image_file in image_files:
                try:
                    os.remove(image_file)
                except OSError as e:
                    print(f"Warning: Failed to delete {image_file}: {e}")
        
        return output_path
    except Exception as e:
        print(f"Error converting to CBZ: {e}")
        return None


def convert_manga_chapters(
    manga_dir: str,
    format: str = "pdf",
    delete_images: bool = False
) -> List[str]:
    """
    Convert all chapters of a manga to the specified format.
    """
    created_files = []
    
    try:
        chapter_dirs = [os.path.join(manga_dir, item) for item in os.listdir(manga_dir) if os.path.isdir(os.path.join(manga_dir, item))]
    except FileNotFoundError:
        print(f"Error: Manga directory not found at {manga_dir}")
        return []
    
    chapter_dirs.sort()
    
    for chapter_dir in chapter_dirs:
        try:
            if format.lower() == "pdf":
                output_file = convert_to_pdf(chapter_dir, delete_images=delete_images)
            elif format.lower() == "cbz":
                output_file = convert_to_cbz(chapter_dir, delete_images=delete_images)
            else:
                print(f"Unsupported format: {format}")
                continue
            
            if output_file:
                created_files.append(output_file)
                print(f"Converted {os.path.basename(chapter_dir)} to {os.path.basename(output_file)}")
        except Exception as e:
            print(f"Error converting {os.path.basename(chapter_dir)}: {e}")
    
    return created_files


def _get_image_files(directory: str) -> List[str]:
    """
    Get all image files in a directory, sorted numerically.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    image_files = []
    
    try:
        for filename in os.listdir(directory):
            if os.path.splitext(filename)[1].lower() in image_extensions:
                image_files.append(os.path.join(directory, filename))
    except FileNotFoundError:
        print(f"Directory not found: {directory}")

    # Sort numerically based on filename (e.g., 1.jpg, 2.jpg, 10.jpg)
    image_files.sort(key=lambda f: int(os.path.splitext(os.path.basename(f))[0]))
    
    return image_files