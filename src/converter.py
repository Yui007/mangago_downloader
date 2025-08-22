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

from .models import Chapter
from .utils import create_directory, sanitize_filename


def convert_to_pdf(
    chapter_dir: str,
    output_path: Optional[str] = None,
    delete_images: bool = False
) -> Optional[str]:
    """
    Convert chapter images to PDF.
    
    Args:
        chapter_dir (str): Directory containing chapter images.
        output_path (Optional[str]): Path for the output PDF file.
            If None, creates a PDF in the same directory.
        delete_images (bool): Whether to delete images after conversion.
        
    Returns:
        Optional[str]: Path to the created PDF file, or None if conversion failed.
    """
    try:
        # Get all image files in the directory
        image_files = _get_image_files(chapter_dir)
        if not image_files:
            print(f"No images found in {chapter_dir}")
            return None
        
        # Sort images by filename to ensure correct order
        image_files.sort()
        
        # Determine output path
        if not output_path:
            # Create PDF in the same directory with the chapter directory name
            chapter_name = os.path.basename(chapter_dir)
            output_path = os.path.join(chapter_dir, f"{chapter_name}.pdf")
        
        # Create PDF using img2pdf
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_files))
        
        # Delete images if requested
        if delete_images:
            for image_file in image_files:
                try:
                    os.remove(image_file)
                except Exception as e:
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
    
    Args:
        chapter_dir (str): Directory containing chapter images.
        output_path (Optional[str]): Path for the output CBZ file.
            If None, creates a CBZ in the same directory.
        delete_images (bool): Whether to delete images after conversion.
        
    Returns:
        Optional[str]: Path to the created CBZ file, or None if conversion failed.
    """
    try:
        # Get all image files in the directory
        image_files = _get_image_files(chapter_dir)
        if not image_files:
            print(f"No images found in {chapter_dir}")
            return None
        
        # Sort images by filename to ensure correct order
        image_files.sort()
        
        # Determine output path
        if not output_path:
            # Create CBZ in the same directory with the chapter directory name
            chapter_name = os.path.basename(chapter_dir)
            output_path = os.path.join(chapter_dir, f"{chapter_name}.cbz")
        
        # Create CBZ file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image_file in image_files:
                # Add file to zip with just the filename (no path)
                arcname = os.path.basename(image_file)
                zipf.write(image_file, arcname)
        
        # Delete images if requested
        if delete_images:
            for image_file in image_files:
                try:
                    os.remove(image_file)
                except Exception as e:
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
    
    Args:
        manga_dir (str): Directory containing manga chapters.
        format (str): Output format ("pdf" or "cbz").
        delete_images (bool): Whether to delete images after conversion.
        
    Returns:
        List[str]: List of paths to the created files.
    """
    created_files = []
    
    # Get all chapter directories
    chapter_dirs = []
    try:
        for item in os.listdir(manga_dir):
            item_path = os.path.join(manga_dir, item)
            if os.path.isdir(item_path):
                chapter_dirs.append(item_path)
    except Exception as e:
        print(f"Error reading manga directory {manga_dir}: {e}")
        return created_files
    
    # Sort chapter directories
    chapter_dirs.sort()
    
    # Convert each chapter
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
                print(f"Converted {chapter_dir} to {output_file}")
        except Exception as e:
            print(f"Error converting {chapter_dir}: {e}")
            continue
    
    return created_files


def _get_image_files(directory: str) -> List[str]:
    """
    Get all image files in a directory.
    
    Args:
        directory (str): Directory to search for images.
        
    Returns:
        List[str]: List of image file paths.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    image_files = []
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(filename)
                if ext.lower() in image_extensions:
                    image_files.append(file_path)
    except Exception as e:
        print(f"Error reading directory {directory}: {e}")
    
    return image_files


def optimize_images(directory: str, quality: int = 100) -> bool:
    """
    Optimize images in a directory by compressing them.
    
    Args:
        directory (str): Directory containing images to optimize.
        quality (int): JPEG quality (1-100).
        
    Returns:
        bool: True if optimization was successful, False otherwise.
    """
    try:
        image_files = _get_image_files(directory)
        if not image_files:
            print(f"No images found in {directory}")
            return False
        
        for image_file in image_files:
            try:
                # Open image
                with Image.open(image_file) as img:
                    # Convert to RGB if necessary (for JPEG)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save with compression
                    img.save(image_file, 'JPEG', quality=quality, optimize=True)
            except Exception as e:
                print(f"Warning: Failed to optimize {image_file}: {e}")
                continue
        
        return True
    except Exception as e:
        print(f"Error optimizing images: {e}")
        return False