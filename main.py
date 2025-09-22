#!/usr/bin/env python3
"""
GarminTurso - Comprehensive Garmin Connect Data Collection
Main application entry point.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import GarminAuthenticator, TursoDatabase, GarminSyncService
from src.collectors import GarminCollector

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/garmin_turso.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='GarminTurso - Comprehensive Garmin Connect Data Collection')
    parser.add_argument('--mode', choices=['bulk', 'sync'], default='bulk',
                        help='Collection mode: bulk (historical) or sync (continuous)')
    parser.add_argument('--days', type=int, default=None,
                        help='Number of days to collect (bulk mode only)')
    parser.add_argument('--sync-interval', type=int, default=300,
                        help='Sync interval in seconds (sync mode only)')

    args = parser.parse_args()

    if args.mode == 'bulk':
        title = "🚀 GarminTurso - Comprehensive Data Collection"
        description = "Production-ready data collection with improved authentication"
    else:
        title = "🔄 GarminTurso - Continuous Sync Mode"
        description = f"Automatic data synchronization every {args.sync_interval} seconds"

    console.print(Panel.fit(
        f"[bold cyan]{title}[/bold cyan]\n"
        f"[dim]{description}[/dim]",
        border_style="cyan"
    ))

    # Get configuration
    email = os.getenv('GARMIN_EMAIL')
    password = os.getenv('GARMIN_PASSWORD')
    db_path = os.getenv('TURSO_DB_PATH', './data/garmin.db')
    days_back = args.days or int(os.getenv('COLLECTION_DAYS', '7'))

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

        if args.mode == 'bulk':
            # Bulk collection mode (original functionality)
            # Authenticate with Garmin Connect
            console.print("[cyan]Authenticating with Garmin Connect...[/cyan]")
            auth = GarminAuthenticator(email, password)
            api = auth.authenticate()
            console.print("[green]✅ Authentication successful[/green]")

            # Initialize collector
            collector = GarminCollector(api, db)

            # Start data collection with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:

                task = progress.add_task(
                    f"[cyan]Collecting comprehensive Garmin data ({days_back} days)...",
                    total=100
                )

                # Run collection
                results = collector.collect_all_data(days_back=days_back)
                progress.update(task, completed=100)

            # Display results
            display_collection_results(results)

            # Store results in database
            console.print("\n[cyan]Storing data in database...[/cyan]")
            store_results_in_database(db, results)
            console.print("[green]✅ Data stored successfully[/green]")

            console.print(f"\n[dim]Database location: {db_path}[/dim]")
            console.print("[green]🎉 Collection completed successfully![/green]")

        else:
            # Continuous sync mode
            console.print("[cyan]Initializing sync service...[/cyan]")
            sync_service = GarminSyncService(
                db=db,
                email=email,
                password=password,
                sync_interval_seconds=args.sync_interval,
                rate_limit_seconds=2
            )

            console.print(f"[green]✅ Starting continuous sync service[/green]")
            console.print(f"[dim]Database: {db_path}[/dim]")
            console.print(f"[dim]Sync interval: {args.sync_interval} seconds[/dim]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]")

            sync_service.run_continuous_sync()

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Collection interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        logger.exception("Fatal error in main application")
        sys.exit(1)
    finally:
        if 'db' in locals():
            db.close()


def display_collection_results(results: dict):
    """Display collection results in a formatted table."""
    stats = results['collection_stats']

    # Main statistics panel
    stats_panel = Panel(
        f"[green]APIs Called:[/green] {stats['total_apis_called']}\n"
        f"[green]Successful:[/green] {stats['successful_apis']}\n"
        f"[green]Success Rate:[/green] {stats['success_rate']:.1f}%\n"
        f"[green]Data Points:[/green] {stats['total_data_points']:,}\n"
        f"[green]Duration:[/green] {stats['duration_seconds']:.1f}s",
        title="📊 Collection Statistics",
        border_style="green"
    )
    console.print(stats_panel)

    # Detailed results table
    table = Table(title="📋 Data Collection Breakdown", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Data Sources", style="green", justify="right")
    table.add_column("Data Points", style="yellow", justify="right")
    table.add_column("Status", style="blue")

    categories = {
        'enhanced_data': 'Enhanced APIs',
        'intraday_data': 'Intraday Arrays',
        'fit_data': 'FIT/GPS Data'
    }

    for key, category_name in categories.items():
        if key in results:
            data = results[key]
            sources = len(data) if isinstance(data, dict) else 0

            # Count data points
            data_points = 0
            if isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, list):
                        data_points += len(value)
                    elif isinstance(value, dict):
                        data_points += len(value)
                    elif value is not None:
                        data_points += 1

            status = "✅ Success" if sources > 0 else "📭 No Data"
            table.add_row(category_name, str(sources), str(data_points), status)

    console.print(f"\n{table}")

    # Data richness comparison
    baseline_points = 71  # Original baseline
    improvement = stats['total_data_points'] / baseline_points if baseline_points > 0 else 0

    if improvement > 50:
        console.print(f"\n[bold green]🏆 Excellent data richness: {improvement:.1f}x baseline improvement![/bold green]")
    elif improvement > 10:
        console.print(f"\n[green]✅ Good data richness: {improvement:.1f}x baseline improvement[/green]")
    else:
        console.print(f"\n[yellow]⚠️ Data richness: {improvement:.1f}x baseline[/yellow]")


def store_results_in_database(db: TursoDatabase, results: dict):
    """Store collection results in database."""
    try:
        # Store collection metadata
        collection_record = {
            'collection_type': 'comprehensive_collection',
            'start_time': results['collection_stats']['start_time'],
            'end_time': results['collection_stats'].get('end_time'),
            'status': 'success',
            'records_collected': results['collection_stats']['total_data_points']
        }

        db.insert_collection_log(collection_record)
        logger.info("Collection metadata stored in database")

        stored_count = 0
        user_id = 1

        # Store enhanced data
        enhanced_data = results.get('enhanced_data', {})

        # Store profile data
        if 'profile' in enhanced_data and enhanced_data['profile']:
            try:
                db.insert_user_profile(enhanced_data['profile'], user_id)
                stored_count += 1
                logger.info("User profile data stored")
            except Exception as e:
                logger.warning(f"Failed to store profile data: {e}")

        # Store daily wellness data
        wellness_categories = [
            'daily_steps', 'floors', 'intensity_minutes', 'heart_rate',
            'rhr', 'hrv', 'stress', 'respiration', 'spo2', 'body_battery'
        ]

        for category in wellness_categories:
            if category in enhanced_data and enhanced_data[category]:
                try:
                    category_count = 0
                    for daily_record in enhanced_data[category]:
                        if 'date' in daily_record and 'data' in daily_record:
                            # Create daily stats record
                            daily_stats = {
                                'date': daily_record['date'],
                                'user_id': user_id,
                                f'{category}_data': daily_record['data']
                            }
                            db.insert_daily_stats(daily_stats, user_id)
                            stored_count += 1
                            category_count += 1
                    logger.info(f"{category} data stored: {category_count} records")
                except Exception as e:
                    logger.warning(f"Failed to store {category} data: {e}")

        # Store activities
        if 'activities' in enhanced_data and enhanced_data['activities']:
            try:
                activity_count = 0
                for activity in enhanced_data['activities']:
                    try:
                        db.insert_activity(activity, user_id)
                        stored_count += 1
                        activity_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to store activity {activity.get('activityId', 'unknown')}: {e}")
                logger.info(f"Activities stored: {activity_count} records")
            except Exception as e:
                logger.warning(f"Failed to store activities: {e}")

        # Store sleep data
        if 'sleep' in enhanced_data and enhanced_data['sleep']:
            try:
                sleep_count = 0
                for sleep_record in enhanced_data['sleep']:
                    if 'sleep_data' in sleep_record:
                        try:
                            sleep_data = sleep_record['sleep_data'].copy()
                            sleep_data['calendar_date'] = sleep_record['date']
                            db.insert_sleep_data(sleep_data, user_id)
                            stored_count += 1
                            sleep_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to store sleep record for {sleep_record.get('date', 'unknown')}: {e}")
                logger.info(f"Sleep data stored: {sleep_count} records")
            except Exception as e:
                logger.warning(f"Failed to store sleep data: {e}")

        # Store health metrics
        health_categories = ['body_composition', 'hydration', 'training_readiness']
        for category in health_categories:
            if category in enhanced_data and enhanced_data[category]:
                for health_record in enhanced_data[category]:
                    if category == 'body_composition' and 'data' in health_record:
                        body_data = health_record['data']
                        body_data['measurement_date'] = health_record['date']
                        db.insert_body_composition(body_data, user_id)
                        stored_count += 1
                logger.info(f"{category} data stored: {len(enhanced_data[category])} records")

        # Store intraday data
        intraday_data = results.get('intraday_data', {})

        # Store heart rate intraday data
        if 'heart_rate_intraday' in intraday_data and intraday_data['heart_rate_intraday']:
            hr_records = []
            for hr_entry in intraday_data['heart_rate_intraday']:
                hr_record = {
                    'user_id': user_id,
                    'timestamp': hr_entry['datetime'],
                    'heart_rate': hr_entry['heart_rate']
                }
                hr_records.append(hr_record)

            if hr_records:
                db.insert_heart_rate_data(hr_records, user_id)
                stored_count += len(hr_records)
                logger.info(f"Heart rate intraday data stored: {len(hr_records)} records")

        # Store stress intraday data
        if 'stress_body_battery_intraday' in intraday_data and intraday_data['stress_body_battery_intraday']:
            stress_records = []
            for stress_entry in intraday_data['stress_body_battery_intraday']:
                if stress_entry.get('type') == 'stress' and 'stress_level' in stress_entry:
                    stress_record = {
                        'user_id': user_id,
                        'timestamp': stress_entry['datetime'],
                        'stress_level': stress_entry['stress_level']
                    }
                    stress_records.append(stress_record)

            if stress_records:
                db.insert_stress_data(stress_records, user_id)
                stored_count += len(stress_records)
                logger.info(f"Stress intraday data stored: {len(stress_records)} records")

        logger.info(f"Successfully stored {stored_count} individual data records")
        logger.info(f"Total collection data points: {results['collection_stats']['total_data_points']}")

    except Exception as e:
        logger.error(f"Error storing results in database: {e}")
        raise


if __name__ == "__main__":
    main()