#!/usr/bin/env python3
"""
FastAPI server for querying Garmin data and generating health reports.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uvicorn
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import TursoDatabase
from report_generator import HealthReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GarminTurso Query API",
    description="API for querying Garmin Connect data and generating health reports",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database connection
db_path = os.getenv('TURSO_DB_PATH', './data/garmin.db')
db = TursoDatabase(db_path)
report_generator = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    global report_generator
    try:
        db.connect()
        report_generator = HealthReportGenerator(db)
        logger.info(f"Connected to database: {db_path}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    db.close()
    logger.info("Database connection closed")

# Existing endpoints (basic functionality)
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GarminTurso Query API",
        "version": "1.0.0",
        "database": db_path,
        "features": ["Data querying", "Health report generation", "Chart creation"],
        "endpoints": {
            "reports": "/reports/generate",
            "summary": "/reports/summary",
            "download": "/reports/download/{report_id}",
            "docs": "/docs"
        }
    }

@app.get("/database/info")
async def database_info():
    """Get database information and statistics."""
    try:
        cursor = db.conn.cursor()

        # Get table counts
        tables_info = {}
        tables = ['daily_stats', 'activities', 'sleep_data', 'heart_rate_data', 'stress_data', 'body_composition']

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_info[table] = count
            except Exception as e:
                tables_info[table] = f"Error: {e}"

        # Get date range
        cursor.execute("SELECT MIN(date), MAX(date) FROM daily_stats")
        date_range = cursor.fetchone()

        return {
            "database_path": db_path,
            "tables": tables_info,
            "date_range": {
                "start": date_range[0] if date_range[0] else None,
                "end": date_range[1] if date_range[1] else None
            },
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Database info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Report generation endpoints
@app.post("/reports/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    user_id: int = Query(1, description="User ID to generate report for"),
    report_type: str = Query("comprehensive", description="Type of report to generate")
):
    """
    Generate a comprehensive health report.

    Args:
        user_id: User ID to generate report for
        report_type: Type of report ('comprehensive', 'summary')

    Returns:
        Report generation status and download information
    """
    try:
        if not report_generator:
            raise HTTPException(status_code=500, detail="Report generator not initialized")

        if report_type == "comprehensive":
            # Generate comprehensive report
            report_path = report_generator.generate_comprehensive_report(user_id)

            return {
                "status": "completed",
                "report_type": report_type,
                "user_id": user_id,
                "report_path": str(report_path),
                "download_url": f"/reports/download/{Path(report_path).name}",
                "generated_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/summary")
async def get_daily_summary(user_id: int = Query(1, description="User ID")):
    """
    Get a quick daily health summary.

    Args:
        user_id: User ID to get summary for

    Returns:
        Daily health summary with key metrics
    """
    try:
        if not report_generator:
            raise HTTPException(status_code=500, detail="Report generator not initialized")

        summary = report_generator.generate_daily_summary(user_id)
        return summary

    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/download/{report_filename}")
async def download_report(report_filename: str):
    """
    Download a generated report file.

    Args:
        report_filename: Name of the report file to download

    Returns:
        File download response
    """
    try:
        reports_dir = Path("./reports")
        report_path = reports_dir / report_filename

        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        # Determine media type based on extension
        if report_path.suffix.lower() == '.pdf':
            media_type = 'application/pdf'
        elif report_path.suffix.lower() == '.html':
            media_type = 'text/html'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            path=str(report_path),
            media_type=media_type,
            filename=report_filename
        )

    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/list")
async def list_reports():
    """
    List all available generated reports.

    Returns:
        List of available report files with metadata
    """
    try:
        reports_dir = Path("./reports")
        reports_dir.mkdir(exist_ok=True)

        reports = []
        for report_file in reports_dir.glob("*"):
            if report_file.is_file():
                stat = report_file.stat()
                reports.append({
                    "filename": report_file.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "download_url": f"/reports/download/{report_file.name}"
                })

        # Sort by creation time, newest first
        reports.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "reports": reports,
            "total_count": len(reports)
        }

    except Exception as e:
        logger.error(f"List reports error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data query endpoints (comprehensive coverage)

@app.get("/data/all")
async def get_all_data(user_id: int = Query(1, description="User ID")):
    """Get a comprehensive overview of all available data."""
    try:
        cursor = db.conn.cursor()

        # Get data counts from all tables
        data_overview = {}

        tables = ['user_profile', 'daily_stats', 'activities', 'sleep_data',
                 'heart_rate_data', 'stress_data', 'body_composition', 'collection_log']

        for table in tables:
            try:
                if table == 'collection_log':
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (user_id,))
                count = cursor.fetchone()[0]
                data_overview[table] = count
            except Exception as e:
                data_overview[table] = f"Error: {e}"

        return {
            "user_id": user_id,
            "data_overview": data_overview,
            "available_endpoints": {
                "user_profile": "/data/profile",
                "daily_stats": "/data/daily-stats?days=30",
                "activities": "/data/activities?limit=50",
                "sleep_data": "/data/sleep?days=30",
                "heart_rate_data": "/data/heart-rate?days=7",
                "stress_data": "/data/stress?days=7",
                "body_composition": "/data/body-composition?days=90",
                "collection_log": "/data/collection-log"
            }
        }

    except Exception as e:
        logger.error(f"All data query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/profile")
async def get_user_profile(user_id: int = Query(1, description="User ID")):
    """Get user profile information."""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT garmin_user_id, display_name, full_name, locale, timezone,
                   measurement_system, created_at, updated_at
            FROM user_profile
            WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User profile not found")

        return {
            "user_id": user_id,
            "garmin_user_id": row[0],
            "display_name": row[1],
            "full_name": row[2],
            "locale": row[3],
            "timezone": row[4],
            "measurement_system": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }

    except Exception as e:
        logger.error(f"Profile query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/daily-stats")
async def get_daily_stats(
    days: int = Query(30, description="Number of days to retrieve"),
    user_id: int = Query(1, description="User ID")
):
    """Get daily statistics and health metrics."""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT date, total_steps, total_distance_meters, active_seconds,
                   calories_total, floors_climbed, resting_heart_rate,
                   avg_stress_level, body_battery_highest, body_battery_lowest,
                   sleep_score, total_sleep_seconds, hydration_ml,
                   respiration_avg, spo2_avg
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (user_id, str(start_date), str(end_date)))

        daily_records = []
        for row in cursor.fetchall():
            daily_records.append({
                "date": row[0],
                "total_steps": row[1],
                "total_distance_meters": row[2],
                "active_seconds": row[3],
                "calories_total": row[4],
                "floors_climbed": row[5],
                "resting_heart_rate": row[6],
                "avg_stress_level": row[7],
                "body_battery_highest": row[8],
                "body_battery_lowest": row[9],
                "sleep_score": row[10],
                "total_sleep_hours": round(row[11] / 3600, 2) if row[11] else None,
                "hydration_ml": row[12],
                "respiration_avg": row[13],
                "spo2_avg": row[14]
            })

        return {"daily_stats": daily_records, "count": len(daily_records)}

    except Exception as e:
        logger.error(f"Daily stats query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/activities")
async def get_activities(
    limit: int = Query(50, description="Number of activities to return"),
    user_id: int = Query(1, description="User ID")
):
    """Get comprehensive activity data."""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT activity_id, activity_name, activity_type, sport_type,
                   start_time_local, duration_seconds, distance_meters,
                   elevation_gain_meters, avg_speed_mps, avg_heart_rate,
                   max_heart_rate, calories, avg_power_watts,
                   training_effect_aerobic, start_latitude, start_longitude,
                   has_polyline, manual_activity, favorite
            FROM activities
            WHERE user_id = ?
            ORDER BY start_time_local DESC
            LIMIT ?
        """, (user_id, limit))

        activities = []
        for row in cursor.fetchall():
            activities.append({
                "activity_id": row[0],
                "activity_name": row[1],
                "activity_type": row[2],
                "sport_type": row[3],
                "start_time": row[4],
                "duration_seconds": row[5],
                "distance_meters": row[6],
                "elevation_gain_meters": row[7],
                "avg_speed_mps": row[8],
                "avg_heart_rate": row[9],
                "max_heart_rate": row[10],
                "calories": row[11],
                "avg_power_watts": row[12],
                "training_effect_aerobic": row[13],
                "start_latitude": row[14],
                "start_longitude": row[15],
                "has_polyline": row[16],
                "manual_activity": row[17],
                "favorite": row[18]
            })

        return {"activities": activities, "count": len(activities)}

    except Exception as e:
        logger.error(f"Activities query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/sleep")
async def get_sleep_data(
    days: int = Query(30, description="Number of days to retrieve"),
    user_id: int = Query(1, description="User ID")
):
    """Get comprehensive sleep data."""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT calendar_date, overall_sleep_score, sleep_quality_score,
                   sleep_recovery_score, deep_sleep_seconds, light_sleep_seconds,
                   rem_sleep_seconds, awake_seconds, sleep_start_timestamp_local,
                   sleep_end_timestamp_local, avg_respiration_value, avg_spo2_value,
                   avg_hrv, time_to_fall_asleep_seconds, restless_moments_count
            FROM sleep_data
            WHERE user_id = ? AND calendar_date BETWEEN ? AND ?
            ORDER BY calendar_date DESC
        """, (user_id, str(start_date), str(end_date)))

        sleep_records = []
        for row in cursor.fetchall():
            total_sleep_hours = (
                (row[4] or 0) + (row[5] or 0) + (row[6] or 0)
            ) / 3600

            sleep_records.append({
                "date": row[0],
                "overall_sleep_score": row[1],
                "sleep_quality_score": row[2],
                "sleep_recovery_score": row[3],
                "deep_sleep_seconds": row[4],
                "light_sleep_seconds": row[5],
                "rem_sleep_seconds": row[6],
                "awake_seconds": row[7],
                "total_sleep_hours": round(total_sleep_hours, 2),
                "sleep_start": row[8],
                "sleep_end": row[9],
                "avg_respiration_value": row[10],
                "avg_spo2_value": row[11],
                "avg_hrv": row[12],
                "time_to_fall_asleep_seconds": row[13],
                "restless_moments_count": row[14]
            })

        return {"sleep_data": sleep_records, "count": len(sleep_records)}

    except Exception as e:
        logger.error(f"Sleep data query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/heart-rate")
async def get_heart_rate_data(
    days: int = Query(7, description="Number of days to retrieve"),
    user_id: int = Query(1, description="User ID")
):
    """Get intraday heart rate data."""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT timestamp, heart_rate
            FROM heart_rate_data
            WHERE user_id = ? AND DATE(timestamp) BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT 10000
        """, (user_id, str(start_date), str(end_date)))

        heart_rate_records = []
        for row in cursor.fetchall():
            heart_rate_records.append({
                "timestamp": row[0],
                "heart_rate": row[1]
            })

        return {"heart_rate_data": heart_rate_records, "count": len(heart_rate_records)}

    except Exception as e:
        logger.error(f"Heart rate data query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/stress")
async def get_stress_data(
    days: int = Query(7, description="Number of days to retrieve"),
    user_id: int = Query(1, description="User ID")
):
    """Get stress level data."""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT timestamp, stress_level
            FROM stress_data
            WHERE user_id = ? AND DATE(timestamp) BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT 10000
        """, (user_id, str(start_date), str(end_date)))

        stress_records = []
        for row in cursor.fetchall():
            stress_records.append({
                "timestamp": row[0],
                "stress_level": row[1]
            })

        return {"stress_data": stress_records, "count": len(stress_records)}

    except Exception as e:
        logger.error(f"Stress data query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/body-composition")
async def get_body_composition_data(
    days: int = Query(90, description="Number of days to retrieve"),
    user_id: int = Query(1, description="User ID")
):
    """Get body composition data."""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT measurement_date, weight_kg, bmi, body_fat_percentage,
                   body_water_percentage, bone_mass_kg, muscle_mass_kg,
                   physique_rating, visceral_fat_rating, metabolic_age, source_type
            FROM body_composition
            WHERE user_id = ? AND DATE(measurement_date) BETWEEN ? AND ?
            ORDER BY measurement_date DESC
        """, (user_id, str(start_date), str(end_date)))

        body_comp_records = []
        for row in cursor.fetchall():
            body_comp_records.append({
                "measurement_date": row[0],
                "weight_kg": row[1],
                "bmi": row[2],
                "body_fat_percentage": row[3],
                "body_water_percentage": row[4],
                "bone_mass_kg": row[5],
                "muscle_mass_kg": row[6],
                "physique_rating": row[7],
                "visceral_fat_rating": row[8],
                "metabolic_age": row[9],
                "source_type": row[10]
            })

        return {"body_composition_data": body_comp_records, "count": len(body_comp_records)}

    except Exception as e:
        logger.error(f"Body composition data query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/collection-log")
async def get_collection_log(limit: int = Query(50, description="Number of log entries to return")):
    """Get data collection log entries."""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT collection_type, start_time, end_time, status,
                   records_collected, error_message, created_at
            FROM collection_log
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        log_entries = []
        for row in cursor.fetchall():
            log_entries.append({
                "collection_type": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "status": row[3],
                "records_collected": row[4],
                "error_message": row[5],
                "created_at": row[6]
            })

        return {"collection_log": log_entries, "count": len(log_entries)}

    except Exception as e:
        logger.error(f"Collection log query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting GarminTurso Query API with Report Generation...")
    print(f"Database: {db_path}")
    print("API will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Report generation: http://localhost:8000/reports/generate")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )