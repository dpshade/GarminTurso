"""
Health report generator for GarminTurso.
Creates comprehensive WHOOP-style health reports from Garmin Connect data.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
import weasyprint
from io import BytesIO
import base64

from ..core.database import TursoDatabase
from .data_processor import DataProcessor
from .charts.core_vitals import CoreVitalsCharts

logger = logging.getLogger(__name__)


class HealthReportGenerator:
    """
    Generate comprehensive health reports with WHOOP-style visualizations.
    """

    def __init__(self, db: TursoDatabase, output_dir: str = "./reports"):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.data_processor = DataProcessor(db)
        self.chart_generator = CoreVitalsCharts()

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def generate_comprehensive_report(self, user_id: int = 1, report_date: Optional[datetime] = None) -> str:
        """
        Generate a comprehensive health report.

        Args:
            user_id: User ID to generate report for
            report_date: Date for the report (defaults to today)

        Returns:
            Path to generated PDF report
        """
        if report_date is None:
            report_date = datetime.now()

        logger.info(f"Generating comprehensive health report for user {user_id}")

        try:
            # Collect all data
            report_data = self._collect_report_data(user_id)

            # Generate all charts
            charts = self._generate_all_charts(report_data)

            # Create HTML report
            html_content = self._create_html_report(report_data, charts, report_date)

            # Generate PDF
            pdf_path = self._generate_pdf_report(html_content, user_id, report_date)

            logger.info(f"Report generated successfully: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def _collect_report_data(self, user_id: int) -> Dict[str, Any]:
        """Collect all data needed for the report."""
        logger.info("Collecting report data...")

        data = {
            'core_vitals_30d': {},
            'core_vitals_180d': {},
            'activity_frequency': []
        }

        # Core vitals - 30 day trends
        core_metrics = ['resting_heart_rate', 'respiratory_rate', 'sleep_duration', 'aerobic_activity']

        for metric in core_metrics:
            try:
                data['core_vitals_30d'][metric] = self.data_processor.get_30_day_trend_data(metric, user_id)
            except Exception as e:
                logger.warning(f"Could not retrieve 30-day data for {metric}: {e}")
                data['core_vitals_30d'][metric] = {}

        # Core vitals - 180 day monthly averages
        for metric in core_metrics:
            try:
                data['core_vitals_180d'][metric] = self.data_processor.get_180_day_monthly_averages(metric, user_id)
            except Exception as e:
                logger.warning(f"Could not retrieve 180-day data for {metric}: {e}")
                data['core_vitals_180d'][metric] = {}

        # Activity frequency
        try:
            data['activity_frequency'] = self.data_processor.get_activity_frequency_data(user_id)
        except Exception as e:
            logger.warning(f"Could not retrieve activity frequency data: {e}")

        return data

    def _generate_all_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all charts and return as base64 encoded images."""
        logger.info("Generating charts...")

        charts = {}

        # 30-day trend charts
        for metric, data in report_data['core_vitals_30d'].items():
            if data:
                try:
                    metric_display_name = metric.replace('_', ' ').title()

                    if metric == 'sleep_duration':
                        fig = self.chart_generator.create_sleep_duration_chart(data)
                    elif metric == 'aerobic_activity':
                        fig = self.chart_generator.create_aerobic_activity_chart(data)
                    else:
                        fig = self.chart_generator.create_30_day_trend_chart(data, metric_display_name)

                    charts[f'{metric}_30d'] = self._fig_to_base64(fig)
                    plt.close(fig)

                except Exception as e:
                    logger.warning(f"Could not generate 30-day chart for {metric}: {e}")

        # 180-day monthly average charts
        for metric, data in report_data['core_vitals_180d'].items():
            if data:
                try:
                    metric_display_name = metric.replace('_', ' ').title()
                    fig = self.chart_generator.create_monthly_averages_chart(data, metric_display_name)
                    charts[f'{metric}_180d'] = self._fig_to_base64(fig)
                    plt.close(fig)

                except Exception as e:
                    logger.warning(f"Could not generate 180-day chart for {metric}: {e}")

        # Activity frequency chart
        if report_data['activity_frequency']:
            try:
                fig = self.chart_generator.create_activity_frequency_chart(report_data['activity_frequency'])
                charts['activity_frequency'] = self._fig_to_base64(fig)
                plt.close(fig)
            except Exception as e:
                logger.warning(f"Could not generate activity frequency chart: {e}")

        logger.info(f"Generated {len(charts)} charts")
        return charts

    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 encoded string."""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return image_base64

    def _create_html_report(self, report_data: Dict[str, Any], charts: Dict[str, str], report_date: datetime) -> str:
        """Create HTML content for the report."""
        logger.info("Creating HTML report...")

        try:
            template = self.jinja_env.get_template('health_report.html')
        except Exception:
            # If template doesn't exist, create a basic one
            template_content = self._get_default_template()
            template = self.jinja_env.from_string(template_content)

        # Prepare template data
        template_data = {
            'report_title': 'Comprehensive Health Report',
            'report_date': report_date.strftime('%B %d, %Y'),
            'report_period': f"{(report_date - timedelta(days=30)).strftime('%B %d')} - {report_date.strftime('%B %d, %Y')}",
            'charts': charts,
            'report_data': report_data,
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        html_content = template.render(**template_data)
        return html_content

    def _generate_pdf_report(self, html_content: str, user_id: int, report_date: datetime) -> Path:
        """Generate PDF from HTML content."""
        logger.info("Generating PDF report...")

        # Create filename
        date_str = report_date.strftime('%Y-%m-%d')
        filename = f"health_report_user_{user_id}_{date_str}.pdf"
        pdf_path = self.output_dir / filename

        try:
            # Generate PDF using WeasyPrint
            html = weasyprint.HTML(string=html_content)
            css = weasyprint.CSS(string=self._get_default_css())
            html.write_pdf(str(pdf_path), stylesheets=[css])

            return pdf_path

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            # Fallback: save as HTML
            html_path = pdf_path.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Saved as HTML instead: {html_path}")
            return html_path

    def _get_default_template(self) -> str:
        """Get default HTML template if none exists."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        {{ css }}
    </style>
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <h1>{{ report_title }}</h1>
            <p class="report-date">{{ report_date }}</p>
            <p class="report-period">Period: {{ report_period }}</p>
        </header>

        <main class="report-content">
            <!-- Core Vitals - 30 Day Trends -->
            <section class="section">
                <h2>Core Vitals – 30-Day Trends</h2>

                {% if charts.resting_heart_rate_30d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.resting_heart_rate_30d }}" alt="Resting Heart Rate 30-Day Trend" />
                </div>
                {% endif %}

                {% if charts.respiratory_rate_30d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.respiratory_rate_30d }}" alt="Respiratory Rate 30-Day Trend" />
                </div>
                {% endif %}

                {% if charts.sleep_duration_30d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.sleep_duration_30d }}" alt="Sleep Duration 30-Day Trend" />
                </div>
                {% endif %}

                {% if charts.aerobic_activity_30d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.aerobic_activity_30d }}" alt="Aerobic Activity 30-Day Trend" />
                </div>
                {% endif %}
            </section>

            <!-- Longitudinal Patterns - 180 Day Monthly Averages -->
            <section class="section">
                <h2>Longitudinal Patterns – 180-Day Monthly Averages</h2>

                {% if charts.resting_heart_rate_180d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.resting_heart_rate_180d }}" alt="Resting Heart Rate 180-Day Averages" />
                </div>
                {% endif %}

                {% if charts.respiratory_rate_180d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.respiratory_rate_180d }}" alt="Respiratory Rate 180-Day Averages" />
                </div>
                {% endif %}

                {% if charts.sleep_duration_180d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.sleep_duration_180d }}" alt="Sleep Duration 180-Day Averages" />
                </div>
                {% endif %}

                {% if charts.aerobic_activity_180d %}
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.aerobic_activity_180d }}" alt="Aerobic Activity 180-Day Averages" />
                </div>
                {% endif %}
            </section>

            <!-- Activity Frequency -->
            {% if charts.activity_frequency %}
            <section class="section">
                <h2>Most Frequently Logged Activities</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ charts.activity_frequency }}" alt="Activity Frequency" />
                </div>
            </section>
            {% endif %}
        </main>

        <footer class="report-footer">
            <p>Generated by GarminTurso on {{ generation_time }}</p>
            <p>🤖 Generated with <a href="https://claude.ai/code">Claude Code</a></p>
        </footer>
    </div>
</body>
</html>
        """

    def _get_default_css(self) -> str:
        """Get default CSS styles."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
        }

        .report-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .report-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }

        .report-header h1 {
            font-size: 2.5em;
            font-weight: bold;
            color: #4c72b0;
            margin-bottom: 10px;
        }

        .report-date {
            font-size: 1.2em;
            color: #666;
            margin-bottom: 5px;
        }

        .report-period {
            font-size: 1em;
            color: #888;
        }

        .section {
            margin-bottom: 50px;
        }

        .section h2 {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .chart-container {
            margin-bottom: 30px;
            text-align: center;
            page-break-inside: avoid;
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }

        .report-footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 0.9em;
        }

        .report-footer a {
            color: #4c72b0;
            text-decoration: none;
        }

        @media print {
            .section {
                page-break-inside: avoid;
            }

            .chart-container {
                page-break-inside: avoid;
            }
        }
        """

    def generate_daily_summary(self, user_id: int = 1) -> Dict[str, Any]:
        """
        Generate a quick daily summary for API endpoints.

        Args:
            user_id: User ID to generate summary for

        Returns:
            Dictionary with key metrics and insights
        """
        try:
            # Get recent data
            rhr_data = self.data_processor.get_30_day_trend_data('resting_heart_rate', user_id)
            sleep_data = self.data_processor.get_30_day_trend_data('sleep_duration', user_id)
            activity_data = self.data_processor.get_activity_frequency_data(user_id, days_back=7)

            summary = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'resting_heart_rate': {
                    'current': rhr_data.get('average', 0),
                    'unit': 'BPM'
                },
                'sleep_duration': {
                    'average': sleep_data.get('average', 0),
                    'unit': 'hours'
                },
                'weekly_activities': len(activity_data),
                'status': 'good' if rhr_data.get('average', 0) > 0 else 'no_data'
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'error',
                'message': str(e)
            }