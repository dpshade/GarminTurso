#!/usr/bin/env python3
"""
Test script for health report generation.
Tests the complete chart generation pipeline with existing data.
"""

import os
import sys
import logging
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console()


def main():
    """Test the health report generation system."""
    console.print(Panel.fit(
        "[bold cyan]🧪 Testing Health Report Generation System[/bold cyan]\n"
        "[dim]Testing charts, data processing, and PDF generation[/dim]",
        border_style="cyan"
    ))

    # Get database path
    db_path = os.getenv('TURSO_DB_PATH', './data/garmin.db')

    if not Path(db_path).exists():
        console.print(f"[red]❌ Database not found: {db_path}[/red]")
        console.print("[yellow]💡 Run the data collection first: python main.py[/yellow]")
        sys.exit(1)

    try:
        # Initialize database and report generator
        console.print("[cyan]Initializing database and report generator...[/cyan]")
        db = TursoDatabase(db_path)
        db.connect()

        report_generator = HealthReportGenerator(db)
        console.print("[green]✅ Report generator initialized[/green]")

        # Test data availability
        console.print("[cyan]Checking data availability...[/cyan]")
        cursor = db.conn.cursor()

        # Check daily stats
        cursor.execute("SELECT COUNT(*) FROM daily_stats")
        daily_stats_count = cursor.fetchone()[0]

        # Check activities
        cursor.execute("SELECT COUNT(*) FROM activities")
        activities_count = cursor.fetchone()[0]

        # Check sleep data
        cursor.execute("SELECT COUNT(*) FROM sleep_data")
        sleep_count = cursor.fetchone()[0]

        console.print(f"[blue]📊 Data Summary:[/blue]")
        console.print(f"  • Daily stats: {daily_stats_count} records")
        console.print(f"  • Activities: {activities_count} records")
        console.print(f"  • Sleep data: {sleep_count} records")

        if daily_stats_count == 0 and activities_count == 0 and sleep_count == 0:
            console.print("[yellow]⚠️ No data found in database[/yellow]")
            console.print("[yellow]💡 Run data collection first: python main.py[/yellow]")
            return

        # Test daily summary generation
        console.print("[cyan]Testing daily summary generation...[/cyan]")
        summary = report_generator.generate_daily_summary(user_id=1)
        console.print(f"[green]✅ Daily summary generated: {summary['status']}[/green]")

        # Test data processor
        console.print("[cyan]Testing data processor...[/cyan]")
        from data_processor import DataProcessor
        processor = DataProcessor(db)

        # Test various data queries
        metrics_tested = 0
        metrics_with_data = 0

        test_metrics = ['resting_heart_rate', 'respiratory_rate', 'sleep_duration', 'aerobic_activity']

        for metric in test_metrics:
            try:
                data_30d = processor.get_30_day_trend_data(metric, user_id=1)
                data_180d = processor.get_180_day_monthly_averages(metric, user_id=1)
                metrics_tested += 1

                if data_30d.get('daily_data') or data_180d.get('monthly_data'):
                    metrics_with_data += 1
                    console.print(f"  ✅ {metric}: Data available")
                else:
                    console.print(f"  📭 {metric}: No data")

            except Exception as e:
                console.print(f"  ❌ {metric}: Error - {e}")

        console.print(f"[blue]📊 Data processor results: {metrics_with_data}/{metrics_tested} metrics have data[/blue]")

        # Test chart generation
        console.print("[cyan]Testing chart generation...[/cyan]")
        from charts.core_vitals import CoreVitalsCharts
        chart_generator = CoreVitalsCharts()

        charts_generated = 0
        charts_successful = 0

        # Test with available data
        for metric in test_metrics:
            try:
                data = processor.get_30_day_trend_data(metric, user_id=1)
                if data.get('daily_data'):
                    if metric == 'sleep_duration':
                        fig = chart_generator.create_sleep_duration_chart(data)
                    elif metric == 'aerobic_activity':
                        fig = chart_generator.create_aerobic_activity_chart(data)
                    else:
                        fig = chart_generator.create_30_day_trend_chart(data, metric.replace('_', ' ').title())

                    if fig:
                        charts_successful += 1
                        # Close to prevent memory issues
                        import matplotlib.pyplot as plt
                        plt.close(fig)

                charts_generated += 1

            except Exception as e:
                console.print(f"  ❌ Chart generation error for {metric}: {e}")

        console.print(f"[blue]📈 Chart generation: {charts_successful}/{charts_generated} charts successful[/blue]")

        # Test activity frequency chart
        try:
            activities = processor.get_activity_frequency_data(user_id=1)
            if activities:
                fig = chart_generator.create_activity_frequency_chart(activities)
                if fig:
                    charts_successful += 1
                    import matplotlib.pyplot as plt
                    plt.close(fig)
                console.print(f"  ✅ Activity frequency chart: Success")
            else:
                console.print(f"  📭 Activity frequency chart: No activity data")
        except Exception as e:
            console.print(f"  ❌ Activity frequency chart error: {e}")

        # Test full report generation
        if metrics_with_data > 0:
            console.print("[cyan]Testing full report generation...[/cyan]")
            try:
                report_path = report_generator.generate_comprehensive_report(user_id=1)
                console.print(f"[green]✅ Full report generated: {report_path}[/green]")

                # Check file size
                report_file = Path(report_path)
                if report_file.exists():
                    file_size = report_file.stat().st_size
                    console.print(f"[blue]📄 Report file size: {file_size:,} bytes[/blue]")
                else:
                    console.print("[yellow]⚠️ Report file not found after generation[/yellow]")

            except Exception as e:
                console.print(f"[red]❌ Full report generation failed: {e}[/red]")
                logger.exception("Full report generation error")
        else:
            console.print("[yellow]⚠️ Skipping full report generation (no data available)[/yellow]")

        # Final assessment
        console.print(f"\n[bold green]🎉 Testing completed![/bold green]")

        if metrics_with_data >= 2 and charts_successful >= 2:
            console.print("[bold green]🏆 EXCELLENT: Report generation system is working well![/bold green]")
        elif metrics_with_data >= 1 and charts_successful >= 1:
            console.print("[green]✅ GOOD: Report generation system is functional[/green]")
        else:
            console.print("[yellow]⚠️ LIMITED: Report generation system needs more data[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error during testing: {e}[/red]")
        logger.exception("Testing error")
        sys.exit(1)

    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()