#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for GarminTurso database.
Provides AI assistants with direct access to Garmin health data.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Sequence

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import TursoDatabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("garmin-mcp-server")

# Initialize the MCP server
server = Server("garmin-turso")

# Global database connection
db: TursoDatabase = None


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for interacting with Garmin data."""
    return [
        types.Tool(
            name="list_tables",
            description="List all available tables in the Garmin database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="describe_table",
            description="Get the schema and column information for a specific table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table"]
            }
        ),
        types.Tool(
            name="execute_query",
            description="Execute a SQL query on the Garmin database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only for safety)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_daily_summary",
            description="Get a summary of daily health metrics for a specific date or recent days",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (optional, defaults to recent data)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of recent days to include (default: 7)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_sleep_analysis",
            description="Get detailed sleep analysis including scores, stages, and trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of recent days to analyze (default: 7)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_activity_summary",
            description="Get summary of activities including types, frequency, and performance metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of recent days to analyze (default: 30)"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """Handle tool calls from AI assistants."""
    if arguments is None:
        arguments = {}

    try:
        if name == "list_tables":
            return await list_tables()
        elif name == "describe_table":
            table = arguments.get("table")
            if not table:
                raise ValueError("Table name is required")
            return await describe_table(table)
        elif name == "execute_query":
            query = arguments.get("query")
            if not query:
                raise ValueError("Query is required")
            return await execute_query(query)
        elif name == "get_daily_summary":
            date = arguments.get("date")
            days = arguments.get("days", 7)
            return await get_daily_summary(date, days)
        elif name == "get_sleep_analysis":
            days = arguments.get("days", 7)
            return await get_sleep_analysis(days)
        elif name == "get_activity_summary":
            days = arguments.get("days", 30)
            return await get_activity_summary(days)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def list_tables() -> list[types.TextContent]:
    """List all tables in the database."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    table_list = "\n".join(f"- {table}" for table in tables)
    return [types.TextContent(
        type="text",
        text=f"Available tables in Garmin database:\n{table_list}"
    )]


async def describe_table(table: str) -> list[types.TextContent]:
    """Describe the schema of a specific table."""
    cursor = db.conn.cursor()

    # Get table schema
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()

    if not columns:
        return [types.TextContent(
            type="text",
            text=f"Table '{table}' not found"
        )]

    # Format column information
    schema_info = f"Schema for table '{table}':\n\n"
    for col in columns:
        cid, name, type_, notnull, default, pk = col
        schema_info += f"- {name}: {type_}"
        if pk:
            schema_info += " (PRIMARY KEY)"
        if notnull:
            schema_info += " NOT NULL"
        if default is not None:
            schema_info += f" DEFAULT {default}"
        schema_info += "\n"

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]
    schema_info += f"\nTotal rows: {row_count:,}"

    return [types.TextContent(type="text", text=schema_info)]


async def execute_query(query: str) -> list[types.TextContent]:
    """Execute a SQL query (SELECT only for safety)."""
    # Safety check - only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return [types.TextContent(
            type="text",
            text="Error: Only SELECT queries are allowed for safety"
        )]

    try:
        cursor = db.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        if not results:
            return [types.TextContent(
                type="text",
                text="Query executed successfully but returned no results"
            )]

        # Format results as a table
        result_text = f"Query: {query}\n\n"
        result_text += " | ".join(columns) + "\n"
        result_text += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"

        for row in results[:100]:  # Limit to 100 rows for readability
            result_text += " | ".join(str(cell) if cell is not None else "NULL" for cell in row) + "\n"

        if len(results) > 100:
            result_text += f"\n... and {len(results) - 100} more rows"

        result_text += f"\nTotal rows: {len(results)}"

        return [types.TextContent(type="text", text=result_text)]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Query error: {str(e)}"
        )]


async def get_daily_summary(date: str | None, days: int) -> list[types.TextContent]:
    """Get daily health summary."""
    cursor = db.conn.cursor()

    if date:
        # Specific date
        cursor.execute("""
            SELECT date, total_steps, calories_total, resting_heart_rate,
                   body_battery_highest, sleep_score, total_sleep_seconds
            FROM daily_stats
            WHERE date = ?
        """, (date,))
    else:
        # Recent days
        cursor.execute("""
            SELECT date, total_steps, calories_total, resting_heart_rate,
                   body_battery_highest, sleep_score, total_sleep_seconds
            FROM daily_stats
            ORDER BY date DESC
            LIMIT ?
        """, (days,))

    results = cursor.fetchall()

    if not results:
        return [types.TextContent(
            type="text",
            text="No daily summary data found for the specified period"
        )]

    summary = "Daily Health Summary:\n\n"
    for row in results:
        date, steps, calories, rhr, bb, sleep_score, sleep_seconds = row
        sleep_hours = sleep_seconds / 3600 if sleep_seconds else 0

        summary += f"📅 {date}:\n"
        if steps:
            summary += f"  👟 Steps: {steps:,}\n"
        if calories:
            summary += f"  🔥 Calories: {calories:,}\n"
        if rhr:
            summary += f"  💓 Resting HR: {rhr} BPM\n"
        if bb:
            summary += f"  🔋 Body Battery Peak: {bb}\n"
        if sleep_score:
            summary += f"  😴 Sleep Score: {sleep_score}\n"
        if sleep_hours > 0:
            summary += f"  🛌 Sleep Duration: {sleep_hours:.1f}h\n"
        summary += "\n"

    return [types.TextContent(type="text", text=summary)]


async def get_sleep_analysis(days: int) -> list[types.TextContent]:
    """Get detailed sleep analysis."""
    cursor = db.conn.cursor()

    cursor.execute("""
        SELECT calendar_date, overall_sleep_score,
               deep_sleep_seconds, light_sleep_seconds, rem_sleep_seconds,
               avg_respiration_value, avg_spo2_value
        FROM sleep_data
        ORDER BY calendar_date DESC
        LIMIT ?
    """, (days,))

    results = cursor.fetchall()

    if not results:
        return [types.TextContent(
            type="text",
            text="No sleep data found for the specified period"
        )]

    analysis = "Sleep Analysis:\n\n"
    total_scores = []
    total_sleep_hours = []

    for row in results:
        date, score, deep, light, rem, resp, spo2 = row

        total_sleep = (deep or 0) + (light or 0) + (rem or 0)
        sleep_hours = total_sleep / 3600 if total_sleep > 0 else 0

        if score:
            total_scores.append(score)
        if sleep_hours > 0:
            total_sleep_hours.append(sleep_hours)

        analysis += f"🌙 {date}:\n"
        if score:
            analysis += f"  📊 Sleep Score: {score}/100\n"
        if sleep_hours > 0:
            analysis += f"  ⏰ Total Sleep: {sleep_hours:.1f}h\n"
            if deep:
                analysis += f"  🛌 Deep: {deep/3600:.1f}h ({deep/total_sleep*100:.0f}%)\n"
            if light:
                analysis += f"  😊 Light: {light/3600:.1f}h ({light/total_sleep*100:.0f}%)\n"
            if rem:
                analysis += f"  🧠 REM: {rem/3600:.1f}h ({rem/total_sleep*100:.0f}%)\n"
        if resp:
            analysis += f"  🫁 Avg Respiration: {resp:.1f} RPM\n"
        if spo2:
            analysis += f"  🩸 Avg SpO2: {spo2:.1f}%\n"
        analysis += "\n"

    # Add summary statistics
    if total_scores:
        avg_score = sum(total_scores) / len(total_scores)
        analysis += f"📈 Average Sleep Score: {avg_score:.1f}/100\n"

    if total_sleep_hours:
        avg_sleep = sum(total_sleep_hours) / len(total_sleep_hours)
        analysis += f"📈 Average Sleep Duration: {avg_sleep:.1f}h\n"

    return [types.TextContent(type="text", text=analysis)]


async def get_activity_summary(days: int) -> list[types.TextContent]:
    """Get activity summary and analysis."""
    cursor = db.conn.cursor()

    # Get activity counts by type
    cursor.execute("""
        SELECT activity_type, COUNT(*) as count,
               AVG(distance_meters) as avg_distance,
               AVG(duration_seconds) as avg_duration,
               AVG(calories) as avg_calories
        FROM activities
        WHERE start_time_local >= date('now', '-{} days')
        GROUP BY activity_type
        ORDER BY count DESC
    """.format(days))

    activity_types = cursor.fetchall()

    # Get recent activities
    cursor.execute("""
        SELECT activity_name, activity_type, start_time_local,
               distance_meters, duration_seconds, calories
        FROM activities
        WHERE start_time_local >= date('now', '-{} days')
        ORDER BY start_time_local DESC
        LIMIT 10
    """.format(days))

    recent_activities = cursor.fetchall()

    summary = f"Activity Summary (Last {days} days):\n\n"

    if activity_types:
        summary += "📊 Activity Types:\n"
        for activity_type, count, avg_dist, avg_dur, avg_cal in activity_types:
            summary += f"  • {activity_type or 'Unknown'}: {count} activities\n"
            if avg_dist and avg_dist > 0:
                summary += f"    📏 Avg Distance: {avg_dist/1000:.1f}km\n"
            if avg_dur and avg_dur > 0:
                summary += f"    ⏱️ Avg Duration: {avg_dur/60:.0f}min\n"
            if avg_cal and avg_cal > 0:
                summary += f"    🔥 Avg Calories: {avg_cal:.0f}\n"
        summary += "\n"

    if recent_activities:
        summary += "🏃 Recent Activities:\n"
        for name, type_, start, distance, duration, calories in recent_activities:
            summary += f"  • {name or type_ or 'Activity'} ({start[:10]})\n"
            if distance and distance > 0:
                summary += f"    📏 {distance/1000:.1f}km"
            if duration and duration > 0:
                summary += f" ⏱️ {duration/60:.0f}min"
            if calories and calories > 0:
                summary += f" 🔥 {calories:.0f}cal"
            summary += "\n"
    else:
        summary += "No recent activities found.\n"

    return [types.TextContent(type="text", text=summary)]


async def main():
    """Main function to run the MCP server."""
    # Initialize database
    global db
    db_path = os.getenv('TURSO_DB_PATH', './data/garmin.db')

    if not Path(db_path).exists():
        logger.error(f"Database not found at {db_path}")
        logger.error("Run 'python main.py' first to collect data from Garmin Connect")
        sys.exit(1)

    db = TursoDatabase(db_path)
    db.connect()
    logger.info(f"Connected to Garmin database at {db_path}")

    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="garmin-turso",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())