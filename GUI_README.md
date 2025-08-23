# Mangago Downloader GUI

A beautiful, modern graphical user interface for the Mangago Downloader project built with PyQt6.

## 🎨 Features

### ✨ Modern Interface
- **Beautiful Dark/Light Theme**: Toggle between stunning dark and light themes
- **Responsive Design**: Adapts to different window sizes
- **Smooth Animations**: Polished hover effects and transitions
- **Glass Morphism**: Modern card-based layout with glass effects

### 🔍 Smart Search
- **Dual Mode Search**: Search by manga title or paste direct URLs
- **Auto-complete**: Search history with intelligent suggestions
- **Pagination**: Browse through multiple pages of results
- **Card Layout**: Beautiful manga cards with cover, author, and metadata

### 📖 Interactive Selection
- **Rich Manga Details**: View detailed information about selected manga
- **Chapter Grid**: Interactive chapter selection with bulk operations
- **Smart Selection**: Select all, ranges, or individual chapters
- **Visual Feedback**: Real-time selection count and status

### ⚙️ Advanced Configuration
- **Multiple Formats**: Choose between Images, PDF, or CBZ output
- **Performance Tuning**: Adjust concurrent downloads and timeouts
- **Custom Locations**: Choose download directories
- **Smart Defaults**: Intelligent default settings

### 📊 Real-time Progress
- **Live Progress Tracking**: See download progress for each chapter
- **Overall Statistics**: Total progress, success/failure counts
- **Speed & ETA**: Real-time download speed and time estimates
- **Visual Indicators**: Color-coded status for easy monitoring

## 🚀 Getting Started

### Prerequisites

Ensure you have all dependencies installed:

```bash
pip install PyQt6 httpx beautifulsoup4 selenium img2pdf Pillow
```

### Launching the GUI

You have several ways to launch the GUI:

#### Option 1: Using the Launcher Script
```bash
python launcher.py --gui
```

#### Option 2: Direct Launch
```bash
python gui/main_gui.py
```

#### Option 3: Using pip (if installed)
```bash
mangago-downloader-gui
```

## 📱 User Interface Guide

### 1. Search Interface
- **Search Mode Toggle**: Switch between "Search by Title" and "Direct URL"
- **Search Input**: Type manga titles or paste URLs
- **Advanced Options**: Access additional search settings
- **Recent Searches**: Quick access to your search history

### 2. Results Browser
- **Grid View**: Browse manga in beautiful card layout
- **Quick Preview**: Hover over cards for additional information
- **Selection**: Click on any manga card to view details
- **Pagination**: Navigate through multiple pages of results

### 3. Manga Details
- **Cover & Info**: View manga cover image and detailed information
- **Chapter List**: Browse all available chapters in a table
- **Bulk Selection**: Use tools to select multiple chapters:
  - **Select All**: Choose all available chapters
  - **Select Range**: Pick chapters from X to Y
  - **Invert Selection**: Flip your current selection
- **Quick Actions**: Download all chapters or just selected ones

### 4. Download Configuration
- **Format Selection**:
  - **Images Only**: Save as individual image files
  - **PDF**: Convert to PDF document for reading
  - **CBZ**: Create comic book archive for comic readers
- **Download Options**:
  - **Location**: Choose where to save files
  - **Threads**: Adjust concurrent downloads (1-20)
  - **Retry Settings**: Configure failed download retries
- **Advanced Settings**: Timeout, overwrite options, and more

### 5. Progress Monitoring
- **Overall Progress**: See total download progress and statistics
- **Individual Chapters**: Monitor each chapter's download status
- **Real-time Stats**: View download speed, ETA, and success rates
- **Control Options**: Pause, resume, or cancel downloads
- **Completion Status**: Clear completed items and view results

## 🎯 Workflow Example

1. **Launch** the GUI using `python launcher.py --gui`
2. **Search** for a manga by typing the title in the search box
3. **Browse** results in the beautiful card layout
4. **Select** a manga by clicking on its card
5. **Choose** which chapters to download using the selection tools
6. **Configure** your preferred output format and settings
7. **Start** the download and monitor progress in real-time
8. **Enjoy** your downloaded manga!

## 🎨 Themes

### Dark Theme (Default)
- Deep space-inspired color palette
- Purple and blue gradients
- Easy on the eyes for long sessions

### Light Theme
- Clean, minimalist design
- High contrast for better readability
- Professional appearance

Switch themes anytime using the theme toggle button in the header!

## ⚡ Performance Tips

### Optimal Settings
- **Concurrent Downloads**: 5-10 threads for best balance
- **Format Choice**: 
  - Use "Images Only" for fastest downloads
  - Use "PDF" for reading on devices
  - Use "CBZ" for comic reader apps

### System Requirements
- **Memory**: 4GB+ RAM recommended for large downloads
- **Storage**: Ensure adequate disk space for downloads
- **Network**: Stable internet connection for best results

## 🔧 Troubleshooting

### Common Issues

#### GUI Won't Start
```bash
# Check if PyQt6 is installed
pip install PyQt6

# Verify Chrome/ChromeDriver
# Download from: https://chromedriver.chromium.org/
```

#### Download Failures
- Check internet connection
- Try reducing concurrent downloads
- Verify the manga URL is valid
- Check available disk space

#### Performance Issues
- Reduce concurrent downloads to 3-5
- Close other applications
- Ensure adequate system memory

### Error Messages

#### "Chrome Driver Error"
Download and install ChromeDriver from the official website and ensure it's in your PATH.

#### "Dependency Error"
Install missing dependencies using pip:
```bash
pip install -r requirements.txt
```

## 🛠️ Development

### Architecture
The GUI follows a modern MVC architecture:

- **Views**: Individual widget components (`search_widget.py`, `results_widget.py`, etc.)
- **Controllers**: Business logic controllers (`controllers.py`)
- **Models**: Data models from the core application
- **Styling**: Centralized theme management (`styles.py`)

### Key Components
- **MainWindow**: Central application window
- **SearchWidget**: Search interface with dual modes
- **ResultsWidget**: Results display with card layout
- **DetailsWidget**: Manga details and chapter selection
- **DownloadWidget**: Download configuration
- **ProgressWidget**: Real-time progress tracking

### Integration
The GUI integrates seamlessly with the existing core modules without modifying any of the original code:

- `src.search` - Manga searching
- `src.downloader` - Chapter downloading  
- `src.converter` - Format conversion
- `src.models` - Data structures

## 🎉 Enjoy!

The Mangago Downloader GUI provides a beautiful, modern, and powerful interface for downloading your favorite manga. The intuitive design makes it easy for anyone to use, while advanced features cater to power users.

**Happy downloading!** 📚✨