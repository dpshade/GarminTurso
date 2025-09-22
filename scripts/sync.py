#!/usr/bin/env python3
"""
GarminTurso Continuous Sync Service
Automatically syncs new data from Garmin Connect to local database.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core import TursoDatabase, GarminSyncService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/garmin_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()


def main():
    """Main sync service entry point."""
    parser = argparse.ArgumentParser(description='GarminTurso Continuous Sync Service')
    parser.add_argument('--mode', choices=['continuous', 'single'], default='continuous',
                        help='Sync mode: continuous (daemon) or single (one-time sync)')
    parser.add_argument('--interval', type=int, default=300,
                        help='Sync interval in seconds (default: 300)')
    parser.add_argument('--rate-limit', type=int, default=2,
                        help='Rate limit between API calls in seconds (default: 2)')

    args = parser.parse_args()

    # Display header
    if args.mode == 'continuous':
        title = "🔄 GarminTurso Continuous Sync Service"
        description = f"Automatically syncs new data every {args.interval} seconds"
    else:
        title = "⚡ GarminTurso Single Sync"
        description = "One-time data synchronization"

    console.print(Panel.fit(
        f"[bold cyan]{title}[/bold cyan]\n"
        f"[dim]{description}[/dim]",
        border_style="cyan"
    ))

    # Get configuration
    email = os.getenv('GARMIN_EMAIL')
    password = os.getenv('GARMIN_PASSWORD')
    db_path = os.getenv('TURSO_DB_PATH', './data/garmin.db')

    if not email or not password:
        console.print("[red]❌ GARMIN_EMAIL and GARMIN_PASSWORD environment variables required[/red]")
        console.print("[yellow]Please set your credentials in the .env file[/yellow]")
        sys.exit(1)

    try:
        # Ensure directories exist
        Path('logs').mkdir(exist_ok=True)
        Path('data').mkdir(exist_ok=True)

        # Initialize database
        console.print("[cyan]Initializing database...[/cyan]")
        db = TursoDatabase(db_path)
        db.connect()
        db.create_schema()
        console.print("[green]✅ Database initialized[/green]")

        # Initialize sync service
        console.print("[cyan]Initializing sync service...[/cyan]")
        sync_service = GarminSyncService(
            db=db,
            email=email,
            password=password,
            sync_interval_seconds=args.interval,
            rate_limit_seconds=args.rate_limit
        )

        # Run sync based on mode
        if args.mode == 'continuous':
            console.print("[green]✅ Starting continuous sync service[/green]")
            console.print(f"[dim]Database: {db_path}[/dim]")
            console.print(f"[dim]Sync interval: {args.interval} seconds[/dim]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]")
            sync_service.run_continuous_sync()
        else:
            console.print("[green]✅ Running single sync[/green]")
            success = sync_service.run_single_sync()
            if success:
                console.print("[green]🎉 Sync completed successfully![/green]")
            else:
                console.print("[yellow]ℹ️ No new data to sync[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Sync service stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        logger.exception("Fatal error in sync service")
        sys.exit(1)
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()