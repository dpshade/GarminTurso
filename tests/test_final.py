#!/usr/bin/env python3
"""Test the final production-ready GarminTurso implementation."""

import os
import sys
import logging
from pathlib import Path
from rich.console import Console
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auth import GarminAuthenticator
from database import TursoDatabase
from garmin_collector import GarminCollector

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()


def main():
    """Test the final implementation."""
    console.print("\n[bold cyan]🧪 Testing Final GarminTurso Implementation[/bold cyan]\n")

    email = os.getenv('GARMIN_EMAIL')
    password = os.getenv('GARMIN_PASSWORD')
    db_path = './data/garmin_final_test.db'

    try:
        # Initialize
        console.print("[cyan]Initializing final implementation...[/cyan]")
        db = TursoDatabase(db_path)
        db.connect()
        db.create_schema()

        # Test improved authentication
        auth = GarminAuthenticator(email, password)
        api = auth.authenticate()
        console.print("[green]✅ Improved authentication working[/green]")

        # Test unified collector
        console.print("[cyan]Testing unified collector (2 days)...[/cyan]")
        collector = GarminCollector(api, db)
        results = collector.collect_all_data(days_back=2)

        # Display results
        stats = results['collection_stats']
        console.print(f"\n[bold green]📊 FINAL IMPLEMENTATION RESULTS[/bold green]")
        console.print(f"APIs called: {stats['total_apis_called']}")
        console.print(f"Successful: {stats['successful_apis']}")
        console.print(f"Success rate: {stats['success_rate']:.1f}%")
        console.print(f"Data points: {stats['total_data_points']:,}")
        console.print(f"Duration: {stats['duration_seconds']:.1f}s")

        # Assess performance
        if stats['success_rate'] >= 60 and stats['total_data_points'] >= 1000:
            console.print(f"\n[bold green]🏆 EXCELLENT: Final implementation performing well![/bold green]")
        elif stats['success_rate'] >= 50 and stats['total_data_points'] >= 500:
            console.print(f"\n[green]✅ GOOD: Final implementation working[/green]")
        else:
            console.print(f"\n[yellow]⚠️ NEEDS IMPROVEMENT: Check configuration[/yellow]")

        # Show data breakdown
        console.print(f"\n[bold blue]📋 DATA BREAKDOWN[/bold blue]")
        for category, data in results.items():
            if category != 'collection_stats' and isinstance(data, dict):
                working_sources = sum(1 for v in data.values() if v)
                total_sources = len(data)
                console.print(f"• {category.replace('_', ' ').title()}: {working_sources}/{total_sources} sources")

        console.print(f"\n[dim]Final test database: {db_path}[/dim]")
        console.print(f"[green]🎉 Final implementation test completed![/green]")

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        logger.exception("Fatal error in final test")
        sys.exit(1)

    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()