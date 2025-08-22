"""
Interactive CLI interface for the Mangago Downloader.
"""
import typer
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.search import search_manga, get_manga_details
from src.downloader import download_manga_chapters, get_chapter_list, close_driver
from src.converter import convert_manga_chapters
from src.models import Manga, Chapter, SearchResult

app = typer.Typer()
console = Console()


@app.command()
def main():
    """
    Interactive CLI for downloading manga from Mangago.
    """
    console.print("[bold blue]Mangago Downloader[/bold blue]")
    console.print("[italic]Download your favorite manga easily![/italic]\n")
    
    while True:
        # Step 1: Choose search method
        console.print("\n[bold]Search Options:[/bold]")
        console.print("1. Search for manga by title")
        console.print("2. Download manga using URL directly")
        
        choice = Prompt.ask(
            "[bold green]Choose an option[/bold green]",
            choices=["1", "2"]
        )
        
        manga = None
        if choice == "1":
            # Search by title
            manga_title = Prompt.ask("[bold green]Enter manga title to search for[/bold green]")
            if not manga_title:
                console.print("[red]Please enter a valid manga title.[/red]")
                continue
            
            # Search for manga
            with console.status("[bold green]Searching for manga...", spinner="dots"):
                try:
                    search_results = search_manga(manga_title)
                    if not search_results:
                        console.print("[yellow]No manga found. Please try another search term.[/yellow]")
                        continue
                except Exception as e:
                    console.print(f"[red]Error searching for manga: {e}[/red]")
                    continue
            
            # Display results in Rich table
            table = Table(title="Search Results")
            table.add_column("Index", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Author", style="green")
            table.add_column("Genres", style="blue")
            table.add_column("Chapters", style="yellow")
            
            for result in search_results:
                genres = ", ".join(result.manga.genres) if isinstance(result.manga.genres, list) else result.manga.genres or "N/A"
                chapters = str(result.manga.total_chapters) if result.manga.total_chapters else "N/A"
                author = result.manga.author if result.manga.author else "N/A"
                
                table.add_row(
                    str(result.index),
                    result.manga.title,
                    author,
                    genres,
                    chapters
                )
            
            console.print(table)
            
            # Prompt to select manga by index
            selected_index = IntPrompt.ask(
                "[bold green]Select manga by index[/bold green]",
                choices=[str(r.index) for r in search_results]
            )
            
            selected_result = next((r for r in search_results if r.index == selected_index), None)
            if not selected_result:
                console.print("[red]Invalid selection.[/red]")
                continue
            
            # Get detailed manga information
            with console.status("[bold green]Fetching manga details...", spinner="dots"):
                try:
                    manga, driver = get_manga_details(selected_result.manga.url)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not fetch detailed manga info: {e}[/yellow]")
                    manga = selected_result.manga  # Use basic info
                    driver = None # No driver to close
        else:
            # Use URL directly
            manga_url = Prompt.ask("[bold green]Enter manga URL[/bold green]")
            if not manga_url:
                console.print("[red]Please enter a valid manga URL.[/red]")
                continue
            
            # Get manga details from URL
            with console.status("[bold green]Fetching manga details...", spinner="dots"):
                try:
                    manga, driver = get_manga_details(manga_url)
                except Exception as e:
                    console.print(f"[red]Error fetching manga details: {e}[/red]")
                    continue
        
        # Step 4: Get chapter list
        if driver:
            with console.status("[bold green]Fetching chapter list...", spinner="dots"):
                try:
                    chapters = get_chapter_list(driver) # Pass the driver
                    if not chapters:
                        console.print("[red]No chapters found for this manga.[/red]")
                        continue
                except Exception as e:
                    console.print(f"[red]Error fetching chapter list: {e}[/red]")
                    continue
                finally:
                    close_driver(driver)
        else:
            console.print("[yellow]Could not get chapter list because manga details failed to load.[/yellow]")
            continue
        
        console.print(f"\n[bold blue]Found {len(chapters)} chapters for {manga.title}[/bold blue]")
        
        # Display chapters in a table
        chapter_table = Table(title="Available Chapters")
        chapter_table.add_column("Index", style="cyan")
        chapter_table.add_column("Chapter Title", style="magenta")
        
        for i, chapter in enumerate(chapters, 1):
            chapter_table.add_row(str(i), chapter.title)
        
        console.print(chapter_table)

        # Step 5: Choose chapters to download
        console.print("\n[bold]Chapter Selection Options:[/bold]")
        console.print("1. Download all chapters")
        console.print("2. Download a range of chapters")
        console.print("3. Download a single chapter")
        
        choice = Prompt.ask(
            "[bold green]Choose an option[/bold green]",
            choices=["1", "2", "3"]
        )
        
        selected_chapters = []
        if choice == "1":
            # Download all chapters
            selected_chapters = chapters
        elif choice == "2":
            # Download a range of chapters
            start = IntPrompt.ask("[bold green]Enter start chapter number[/bold green]")
            end = IntPrompt.ask("[bold green]Enter end chapter number[/bold green]")
            
            # Filter chapters in range
            selected_chapters = [ch for ch in chapters if start <= ch.number <= end]
            if not selected_chapters:
                console.print("[yellow]No chapters found in the specified range.[/yellow]")
                continue
        elif choice == "3":
            # Download a single chapter
            chapter_num = IntPrompt.ask("[bold green]Enter chapter number[/bold green]")
            selected_chapters = [ch for ch in chapters if ch.number == chapter_num]
            if not selected_chapters:
                console.print("[yellow]Chapter not found.[/yellow]")
                continue
        
        # Step 6: Select output format
        format_choice = Prompt.ask(
            "[bold green]Select output format[/bold green]",
            choices=["pdf", "cbz"],
            default="pdf"
        )
        
        # Step 7: Ask about deleting images after conversion
        delete_images = Confirm.ask(
            "[bold green]Delete images after conversion?[/bold green]",
            default=False
        )
        
        # Step 8: Download chapters with progress bar
        console.print(f"\n[bold blue]Downloading {len(selected_chapters)} chapters...[/bold blue]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                # Create a task for overall progress
                overall_task = progress.add_task(
                    "[cyan]Downloading chapters...",
                    total=len(selected_chapters)
                )
                
                # Download chapters
                results = download_manga_chapters(
                    manga=manga,
                    chapters=selected_chapters,
                    max_workers=5,
                    download_dir="downloads"
                )
                
                # Update progress
                completed = sum(1 for r in results if r.success)
                progress.update(overall_task, completed=completed)
                
                # Show results
                successful = [r for r in results if r.success]
                failed = [r for r in results if not r.success]
                
                console.print(f"\n[bold green]Successfully downloaded {len(successful)} chapters[/bold green]")
                if failed:
                    console.print(f"[yellow]Failed to download {len(failed)} chapters[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Error during download: {e}[/red]")
            continue
        
        # Convert to selected format
        if format_choice in ["pdf", "cbz"]:
            console.print(f"\n[bold blue]Converting to {format_choice.upper()}...[/bold blue]")
            
            try:
                manga_dir = os.path.join("downloads", manga.title)
                if os.path.exists(manga_dir):
                    with console.status("[bold green]Converting chapters...", spinner="dots"):
                        created_files = convert_manga_chapters(
                            manga_dir=manga_dir,
                            format=format_choice,
                            delete_images=delete_images
                        )
                    
                    console.print(f"[bold green]Successfully converted {len(created_files)} chapters to {format_choice.upper()}[/bold green]")
                else:
                    console.print("[yellow]Manga directory not found for conversion.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error during conversion: {e}[/red]")
        
        # Ask if user wants to download another manga
        if not Confirm.ask("\n[bold green]Would you like to download another manga?[/bold green]"):
            break
    
    console.print("\n[bold blue]Thank you for using Mangago Downloader! 📚[/bold blue]")


if __name__ == "__main__":
    app()