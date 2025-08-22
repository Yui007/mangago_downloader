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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from urllib.parse import urlparse # Add this import
from src.search import search_manga, get_manga_details
from src.downloader import ChapterDownloader, fetch_chapter_image_urls, get_chapter_list, close_driver
from src.converter import convert_manga_chapters
from src.models import Manga, Chapter, SearchResult
from src.utils import sanitize_filename

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
        manga: Optional[Manga] = None
        chapters: List[Chapter] = []
        selected_chapters: List[Chapter] = []
        driver = None

        try:
            console.print("\n[bold]Search Options:[/bold]")
            console.print("1. Search for manga by title")
            console.print("2. Download manga using URL directly")
            
            choice = Prompt.ask("[bold green]Choose an option[/bold green]", choices=["1", "2"])
            
            if choice == "1":
                manga_title = Prompt.ask("[bold green]Enter manga title to search for[/bold green]")
                if not manga_title:
                    console.print("[red]Please enter a valid manga title.[/red]")
                    continue
                
                page = 1
                while True: # Loop for pagination
                    with console.status(f"[bold green]Searching for '{manga_title}' (Page {page})...[/bold green]"):
                        search_results = search_manga(manga_title, page=page)
                    
                    if not search_results:
                        console.print("[yellow]No more results found.[/yellow]")
                        page = max(1, page - 1)
                        continue

                    table = Table(title=f"Search Results - Page {page}")
                    table.add_column("Index", style="cyan", no_wrap=True)
                    table.add_column("Title", style="magenta")
                    table.add_column("Author", style="green")
                    table.add_column("Chapters", style="yellow")
                    
                    for result in search_results:
                        table.add_row(
                            str(result.index),
                            result.manga.title,
                            result.manga.author or "N/A",
                            str(result.manga.total_chapters) or "N/A"
                        )
                    console.print(table)
                    
                    prompt_choices = [str(r.index) for r in search_results] + ["n", "p"]
                    prompt_text = "[bold green]Select manga by index, 'n' for next page, 'p' for previous page[/bold green]"
                    user_input = Prompt.ask(prompt_text, choices=prompt_choices)

                    if user_input.lower() == 'n':
                        page += 1
                        continue
                    elif user_input.lower() == 'p':
                        page = max(1, page - 1)
                        continue
                    
                    selected_index = int(user_input)
                    selected_result = next((r for r in search_results if r.index == selected_index), None)
                    
                    if not selected_result:
                        console.print("[red]Invalid selection.[/red]")
                        continue
                    
                    with console.status("[bold green]Fetching manga details...", spinner="dots"):
                        manga, driver = get_manga_details(selected_result.manga.url)
                    break 

            else: # choice == "2"
                manga_url = Prompt.ask("[bold green]Enter manga URL[/bold green]")
                if not manga_url:
                    console.print("[red]Please enter a valid manga URL.[/red]")
                    continue

                with console.status("[bold green]Fetching manga details...", spinner="dots"):
                    manga, driver = get_manga_details(manga_url)

            if driver:
                with console.status("[bold green]Fetching chapter list...", spinner="dots"):
                    chapters = get_chapter_list(driver)
                close_driver(driver)
                driver = None

                if not chapters:
                    console.print("[red]No chapters found for this manga.[/red]")
                    continue
            
            console.print(f"\n[bold blue]Found {len(chapters)} chapters for {manga.title}[/bold blue]")
            chapter_table = Table(title="Available Chapters")
            chapter_table.add_column("Index", style="cyan")
            chapter_table.add_column("Chapter Title", style="magenta")
            for i, chapter in enumerate(chapters, 1):
                chapter_table.add_row(str(i), chapter.title)
            console.print(chapter_table)

            console.print("\n[bold]Chapter Selection Options:[/bold]")
            console.print("1. Download all chapters")
            console.print("2. Download a range of chapters (by index)")
            console.print("3. Download a single chapter (by index)")
            
            dl_choice = Prompt.ask("[bold green]Choose an option[/bold green]", choices=["1", "2", "3"])

            if dl_choice == "1":
                selected_chapters = chapters
            elif dl_choice == "2":
                start = IntPrompt.ask("[bold green]Enter start chapter index[/bold green]")
                end = IntPrompt.ask("[bold green]Enter end chapter index[/bold green]")
                try:
                    selected_chapters = chapters[start-1:end]
                except (ValueError, IndexError):
                     console.print("[yellow]Invalid chapter index range.[/yellow]")
                     continue
            elif dl_choice == "3":
                chapter_idx = IntPrompt.ask("[bold green]Enter chapter index[/bold green]")
                try:
                    selected_chapters = [chapters[chapter_idx-1]]
                except (ValueError, IndexError):
                    console.print("[yellow]Invalid chapter index.[/yellow]")
                    continue
            
            if not selected_chapters:
                console.print("[yellow]No chapters selected for download.[/yellow]")
                continue
            
            format_choice = Prompt.ask("[bold green]Select output format[/bold green]", choices=["pdf", "cbz", "none"], default="pdf")
            
            delete_images = False
            if format_choice != "none":
                delete_images = Confirm.ask("[bold green]Delete images after conversion?[/bold green]", default=False)

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
                task = progress.add_task("[cyan]Fetching image URLs...", total=len(selected_chapters))
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_chapter = {executor.submit(fetch_chapter_image_urls, chapter.url): chapter for chapter in selected_chapters}
                    for future in as_completed(future_to_chapter):
                        chapter = future_to_chapter[future]
                        try:
                            chapter.image_urls = future.result()
                            console.print(f"  [green]Found {len(chapter.image_urls)} images for Chapter {chapter.number}.[/green]")
                        except Exception as e:
                            console.print(f"  [red]Error fetching URLs for Chapter {chapter.number}: {e}[/red]")
                        progress.update(task, advance=1)

            console.print(f"\n[bold blue]Downloading {len(selected_chapters)} chapters...[/bold blue]")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
                task = progress.add_task("[cyan]Downloading chapters...", total=len(selected_chapters))
                
                downloader = ChapterDownloader(max_workers=10)
                results = downloader.download_chapters(manga, selected_chapters)
                downloader.close()
                
                progress.update(task, completed=len(results))
                
                successful = [r for r in results if r.success]
                failed = [r for r in results if not r.success]
                
                console.print(f"\n[bold green]Successfully downloaded {len(successful)} chapters[/bold green]")
                if failed:
                    console.print(f"[yellow]Failed to download {len(failed)} chapters[/yellow]")
                    for res in failed:
                        console.print(f"[red]  - Chapter {res.chapter.number}: {res.error_message}[/red]")
            
            if format_choice in ["pdf", "cbz"] and successful:
                console.print(f"\n[bold blue]Converting to {format_choice.upper()}...[/bold blue]")
                with console.status("[bold green]Converting chapters...", spinner="dots"):
                    manga_dir = os.path.join("downloads", sanitize_filename(manga.title))
                    created_files = convert_manga_chapters(manga_dir, format_choice, delete_images)
                    console.print(f"[bold green]Successfully converted {len(created_files)} chapters.[/bold green]")
            elif format_choice == "none":
                console.print("\n[bold blue]Skipping conversion. Images saved.[/bold blue]")

        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        finally:
            if driver:
                close_driver(driver)

        if not Confirm.ask("\n[bold green]Would you like to download another manga?[/bold green]"):
            break
    
    console.print("\n[bold blue]Thank you for using Mangago Downloader! 📚[/bold blue]")


if __name__ == "__main__":
    app()