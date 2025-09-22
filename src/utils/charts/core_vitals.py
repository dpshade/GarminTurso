"""
Core vitals charts module.
Implements WHOOP-style charts for RHR, HRV, Respiratory Rate, and other core metrics.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# WHOOP-style color palette (color-blind safe)
COLORS = {
    'blue': '#4c72b0',
    'green': '#55a868',
    'red': '#c44e52',
    'purple': '#8172b2',
    'tan': '#ccb974',
    'gray': '#7f7f7f',
    'reference_gray': '#e0e0e0',
    'black': '#000000'
}

class CoreVitalsCharts:
    """
    Generate core vital signs charts using WHOOP visual grammar.
    """

    def __init__(self, figsize=(12, 8)):
        self.figsize = figsize
        # Set global style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette([COLORS['blue'], COLORS['green'], COLORS['red'], COLORS['purple']])

    def create_30_day_trend_chart(self, data: Dict[str, Any], metric_name: str) -> plt.Figure:
        """
        Create a 30-day trend chart with reference band and daily line.

        Args:
            data: Dictionary containing daily_data, reference_band, average, unit
            metric_name: Name of the metric for title

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Extract data
        daily_data = data.get('daily_data', [])
        reference_band = data.get('reference_band', {})
        average = data.get('average', 0)
        unit = data.get('unit', '')

        if not daily_data:
            logger.warning(f"No data available for {metric_name}")
            return fig

        # Convert to pandas for easier handling
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Plot reference band (6-month envelope)
        if reference_band.get('min') and reference_band.get('max'):
            ax.fill_between(
                df['date'],
                reference_band['min'],
                reference_band['max'],
                alpha=0.3,
                color=COLORS['reference_gray'],
                label='6-month range'
            )

        # Plot daily values as solid black line
        ax.plot(
            df['date'],
            df['value'],
            color=COLORS['black'],
            linewidth=2,
            marker='o',
            markersize=3,
            label='Daily value'
        )

        # Add average annotation
        if average > 0:
            ax.axhline(
                y=average,
                color=COLORS['gray'],
                linestyle='--',
                alpha=0.7,
                label=f'30-day avg: {average} {unit}'
            )

            # Add average callout box
            ax.text(
                df['date'].iloc[-1],
                average,
                f'{average}\n{unit}',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS['reference_gray'], alpha=0.8),
                ha='right',
                va='center',
                fontsize=12,
                fontweight='bold'
            )

        # Format x-axis
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        ax.set_xlabel('Day of Month', fontsize=10)

        # Format y-axis
        ax.set_ylabel(f'{metric_name} ({unit})', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Set title
        ax.set_title(f'{metric_name.upper()} – 30-DAY TREND',
                    fontsize=14, fontweight='bold', pad=20)

        # Clean up layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

        return fig

    def create_monthly_averages_chart(self, data: Dict[str, Any], metric_name: str) -> plt.Figure:
        """
        Create a 180-day monthly averages chart with dots and connecting lines.

        Args:
            data: Dictionary containing monthly_data, overall_average, unit
            metric_name: Name of the metric for title

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        # Extract data
        monthly_data = data.get('monthly_data', [])
        overall_average = data.get('overall_average', 0)
        unit = data.get('unit', '')

        if not monthly_data:
            logger.warning(f"No monthly data available for {metric_name}")
            return fig

        # Convert to pandas
        df = pd.DataFrame(monthly_data)

        # Create month labels
        month_labels = []
        for month_str in df['month']:
            date_obj = datetime.strptime(month_str, '%Y-%m')
            month_labels.append(date_obj.strftime('%b'))

        # Plot dots and connecting line
        x_positions = range(len(monthly_data))
        ax.plot(
            x_positions,
            df['average'],
            color=COLORS['black'],
            linewidth=2,
            marker='o',
            markersize=8,
            markerfacecolor=COLORS['gray'],
            markeredgecolor=COLORS['black'],
            markeredgewidth=1
        )

        # Add overall average line
        if overall_average > 0:
            ax.axhline(
                y=overall_average,
                color=COLORS['gray'],
                linestyle='-',
                alpha=0.7,
                linewidth=1,
                label=f'6-month avg: {overall_average} {unit}'
            )

        # Add value labels below each dot
        for i, (x, y) in enumerate(zip(x_positions, df['average'])):
            ax.text(x, y - (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05,
                   f'{y}', ha='center', va='top', fontsize=9, color=COLORS['gray'])

        # Format x-axis
        ax.set_xticks(x_positions)
        ax.set_xticklabels(month_labels)
        ax.set_xlabel('Month', fontsize=10)

        # Format y-axis
        ax.set_ylabel(f'{metric_name} ({unit})', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Set title
        ax.set_title(f'{metric_name.upper()} – 180-DAY MONTHLY AVERAGES',
                    fontsize=14, fontweight='bold', pad=20)

        # Clean up layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

        return fig

    def create_sleep_duration_chart(self, data: Dict[str, Any]) -> plt.Figure:
        """
        Create sleep duration chart with stacked areas for nap and night sleep.

        Args:
            data: Dictionary containing daily_data with night_sleep_hours and nap_hours

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        daily_data = data.get('daily_data', [])
        reference_line = data.get('reference_line', 7.0)
        average = data.get('average', 0)

        if not daily_data:
            logger.warning("No sleep data available")
            return fig

        # Convert to pandas
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Create stacked areas
        ax.fill_between(
            df['date'],
            0,
            df['nap_hours'],
            alpha=0.7,
            color=COLORS['purple'],
            label='Nap'
        )

        ax.fill_between(
            df['date'],
            df['nap_hours'],
            df['nap_hours'] + df['night_sleep_hours'],
            alpha=0.7,
            color=COLORS['blue'],
            label='Night sleep'
        )

        # Add recommended line
        ax.axhline(
            y=reference_line,
            color=COLORS['gray'],
            linestyle='--',
            alpha=0.8,
            label=f'Recommended: {reference_line}h'
        )

        # Add average annotation
        if average > 0:
            # Position average text in upper area
            ax.text(
                df['date'].iloc[-5],
                average - 0.5,
                f'{average}h',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                fontsize=12,
                fontweight='bold'
            )

        # Format axes
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        ax.set_xlabel('Day of Month', fontsize=10)
        ax.set_ylabel('Sleep Duration (hours)', fontsize=10)
        ax.set_ylim(0, 12)

        # Title and legend
        ax.set_title('SLEEP DURATION – 30-DAY TREND',
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right')

        # Clean up layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

        return fig

    def create_aerobic_activity_chart(self, data: Dict[str, Any]) -> plt.Figure:
        """
        Create aerobic activity chart with stacked bars for moderate/vigorous minutes.

        Args:
            data: Dictionary containing daily_data with moderate_minutes and vigorous_minutes

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        daily_data = data.get('daily_data', [])
        reference_lines = data.get('reference_lines', {})
        average = data.get('average', 0)

        if not daily_data:
            logger.warning("No aerobic activity data available")
            return fig

        # Convert to pandas
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Create stacked bars
        width = 0.8
        x_positions = range(len(df))

        ax.bar(
            x_positions,
            df['moderate_minutes'],
            width=width,
            color=COLORS['green'],
            alpha=0.7,
            label='Moderate (50-80% HRmax)'
        )

        ax.bar(
            x_positions,
            df['vigorous_minutes'],
            width=width,
            bottom=df['moderate_minutes'],
            color=COLORS['red'],
            alpha=0.7,
            label='Vigorous (80-100% HRmax)'
        )

        # Add reference lines
        if reference_lines.get('moderate_weekly'):
            daily_moderate_target = reference_lines['moderate_weekly'] / 7
            ax.axhline(
                y=daily_moderate_target,
                color=COLORS['green'],
                linestyle='--',
                alpha=0.8,
                label=f'{reference_lines["moderate_weekly"]} min/wk moderate'
            )

        if reference_lines.get('vigorous_weekly'):
            daily_vigorous_target = reference_lines['vigorous_weekly'] / 7
            ax.axhline(
                y=daily_vigorous_target,
                color=COLORS['red'],
                linestyle='--',
                alpha=0.8,
                label=f'{reference_lines["vigorous_weekly"]} min/wk vigorous'
            )

        # Add average annotation
        if average > 0:
            ax.text(
                len(df) * 0.9,
                average + 5,
                f'{average} min',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                fontsize=12,
                fontweight='bold'
            )

        # Format x-axis (simplified for daily bars)
        step = max(1, len(df) // 10)  # Show ~10 labels max
        ax.set_xticks(x_positions[::step])
        ax.set_xticklabels([d.strftime('%d') for d in df['date'].iloc[::step]])
        ax.set_xlabel('Day of Month', fontsize=10)

        # Format y-axis
        ax.set_ylabel('Activity Minutes', fontsize=10)
        ax.set_ylim(0, 180)

        # Title and legend
        ax.set_title('DAILY AEROBIC ACTIVITY – 30-DAY TREND',
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right')

        # Clean up layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()

        return fig

    def create_activity_frequency_chart(self, activities: List[Dict[str, Any]]) -> plt.Figure:
        """
        Create horizontal lollipop chart for most frequent activities.

        Args:
            activities: List of dicts with activity_type and frequency

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        if not activities:
            logger.warning("No activity frequency data available")
            return fig

        # Prepare data
        activity_names = [a['activity_type'] for a in activities]
        frequencies = [a['frequency'] for a in activities]

        # Create horizontal lollipop chart
        y_positions = range(len(activities))

        # Draw lines (stems)
        for i, freq in enumerate(frequencies):
            ax.plot([0, freq], [i, i], color=COLORS['gray'], linewidth=2, alpha=0.7)

        # Draw circles (lollipops)
        ax.scatter(frequencies, y_positions,
                  color=COLORS['blue'], s=80, zorder=5)

        # Add frequency labels
        for i, freq in enumerate(frequencies):
            ax.text(freq + max(frequencies) * 0.02, i, f'{freq}×',
                   va='center', fontsize=11, fontweight='bold')

        # Format axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels([name.replace('_', ' ').title() for name in activity_names])
        ax.set_xlabel('Frequency', fontsize=10)
        ax.set_xlim(0, max(frequencies) * 1.2)

        # Invert y-axis so most frequent is at top
        ax.invert_yaxis()

        # Title
        ax.set_title('MOST FREQUENTLY LOGGED ACTIVITIES',
                    fontsize=14, fontweight='bold', pad=20)

        # Clean up layout
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()

        return fig