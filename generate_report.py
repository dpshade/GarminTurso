#!/usr/bin/env python3
"""
CLI script to generate health reports directly.
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import TursoDatabase
from report_generator import HealthReportGenerator

# Load environment variables
load_dotenv()

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Generate health reports from Garmin data")
    parser.add_argument("--user-id", type=int, default=1, help="User ID to generate report for")
    parser.add_argument("--output-dir", default="./reports", help="Output directory for reports")
    parser.add_argument("--db-path", default=None, help="Database path (defaults to TURSO_DB_PATH env var)")

    args = parser.parse_args()

    # Get database path
    db_path = args.db_path or os.getenv('TURSO_DB_PATH', './data/garmin.db')

    if not Path(db_path).exists():
        console.print(f"[red]❌ Database not found: {db_path}[/red]")
        console.print("[yellow]💡 Run data collection first: python main.py[/yellow]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold cyan]📊 Generating Health Report[/bold cyan]\n"
        f"[dim]User ID: {args.user_id} | Database: {db_path}[/dim]",
        border_style="cyan"
    ))

    try:
        # Initialize database and report generator
        db = TursoDatabase(db_path)
        db.connect()

        report_generator = HealthReportGenerator(db, args.output_dir)

        # Generate comprehensive report
        report_path = report_generator.generate_comprehensive_report(args.user_id)

        # Get file size
        file_size = Path(report_path).stat().st_size

        console.print(f"[green]✅ Report generated successfully![/green]")
        console.print(f"[blue]📄 Report: {report_path}[/blue]")
        console.print(f"[blue]💾 Size: {file_size:,} bytes[/blue]")

        # Generate daily summary
        summary = report_generator.generate_daily_summary(args.user_id)
        console.print(f"\n[bold blue]📋 Daily Summary:[/bold blue]")
        if summary.get('sleep_duration', {}).get('average'):
            console.print(f"  • Average sleep: {summary['sleep_duration']['average']}h")
        if summary.get('weekly_activities'):
            console.print(f"  • Weekly activities: {summary['weekly_activities']}")
        console.print(f"  • Status: {summary['status']}")

    except Exception as e:
        console.print(f"[red]❌ Error generating report: {e}[/red]")
        sys.exit(1)
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()