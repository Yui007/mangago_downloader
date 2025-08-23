#!/usr/bin/env python3
"""
Launcher script for Mangago Downloader.
Provides easy access to both CLI and GUI interfaces.
"""

import sys
import os
import argparse

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="Mangago Downloader - Modern manga downloading tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py --gui           # Launch GUI interface
  python launcher.py --cli           # Launch CLI interface (default)
  python launcher.py --help          # Show this help message

For more information, visit: https://github.com/Yui007/mangago_downloader
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--gui", 
        action="store_true", 
        help="Launch the GUI interface"
    )
    group.add_argument(
        "--cli", 
        action="store_true", 
        help="Launch the CLI interface (default)"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="Mangago Downloader 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Default to CLI if no interface specified
    if not args.gui and not args.cli:
        args.cli = True
    
    if args.gui:
        print("🎨 Launching GUI interface...")
        try:
            from gui.main_gui import main as gui_main
            return gui_main()
        except ImportError as e:
            print(f"❌ Failed to launch GUI: {e}")
            print("📦 Make sure PyQt6 is installed: pip install PyQt6")
            return 1
        except Exception as e:
            print(f"❌ GUI launch error: {e}")
            return 1
    
    elif args.cli:
        print("⌨️  Launching CLI interface...")
        try:
            from cli.main_cli import app
            app()
            return 0
        except ImportError as e:
            print(f"❌ Failed to launch CLI: {e}")
            print("📦 Make sure dependencies are installed: pip install -e .")
            return 1
        except Exception as e:
            print(f"❌ CLI launch error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())