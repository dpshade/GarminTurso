# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GarminTurso is a Python application that collects comprehensive Garmin Connect health data and stores it in a Turso/SQLite database. It features production-ready authentication, comprehensive data collection from 25+ Garmin APIs, and provides both REST API and MCP (Model Context Protocol) interfaces for data access.

## Common Commands

### Development Setup
```bash
# Install dependencies
uv sync

# Setup environment (copy and edit .env)
cp .env.example .env
```

### Data Collection
```bash
# Bulk data collection (historical data, default mode)
python main.py
python main.py --mode bulk --days 30

# Continuous sync mode (automatic updates)
python main.py --mode sync --sync-interval 300

# Dedicated sync service (recommended for continuous operation)
python sync.py --mode continuous --interval 300
python sync.py --mode single  # One-time sync check

# Test database functionality
python test_final.py

# Generate reports
python generate_report.py
```

### API Services
```bash
# Start REST API server
python query_api.py
# Access at http://localhost:8000, docs at http://localhost:8000/docs

# Start MCP server (for AI integrations)
python mcp_server.py
```

### Testing and Reports
```bash
# Run comprehensive tests
python test_reports.py

# Test MCP functionality
./test_mcp.sh

# Setup MCP integration
./setup_mcp.sh
```

## Architecture

### Core Components

**Data Collection Pipeline:**
- `main.py` - Entry point supporting both bulk and continuous sync modes
- `sync.py` - Dedicated continuous sync service (recommended for automation)
- `src/auth.py` - GarminAuthenticator using production-tested garmin_login() approach
- `src/garmin_collector.py` - Main collector combining enhanced APIs, intraday data, and FIT processing
- `src/sync_service.py` - Continuous sync service with automatic data detection
- `src/enhanced_collector.py` - Enhanced API data collection (15/16 endpoints working)
- `src/intraday_collector.py` - High-resolution timestamped data extraction
- `src/fit_processor.py` - GPS coordinates and activity details from GPX exports

**Data Storage:**
- `src/database.py` - TursoDatabase class managing SQLite/Turso operations
- `src/data_processor.py` - Data transformation and validation utilities

**Data Access:**
- `query_api.py` - FastAPI REST interface with 25+ endpoints
- `mcp_server.py` - Model Context Protocol server for AI integrations
- `src/report_generator.py` - Chart and report generation using matplotlib/plotly

### Database Schema
10 specialized tables storing comprehensive health data:
- `user_profile` - User information and preferences
- `daily_stats` - Daily aggregated health metrics
- `activities` - Detailed workout/activity data with GPS
- `sleep_data` - Comprehensive sleep tracking
- `body_composition` - Weight and body metrics
- `heart_rate_data` - Intraday heart rate measurements
- `stress_data` - Stress level measurements
- `collection_log` - Data collection audit trail
- `sync_metadata` - Sync tracking and last sync timestamps
- `metadata` - System metadata and statistics

### Key Features

**Authentication System:**
- Uses production-tested `garmin_login()` approach from garmin-grafana
- Handles MFA with two-step authentication
- Persistent token management in `~/.garminconnect/`
- Automatic session resumption

**Data Collection:**
- 80% API success rate (20/25 APIs working)
- Collects 1,800+ data points in ~40 seconds
- Rate-limited to respect Garmin's API (1.0-1.5s delays)
- Robust error handling with detailed logging
- **Continuous sync mode**: Automatically detects and syncs new data
- **Smart sync**: Only fetches data newer than last successful sync

**Multiple Access Methods:**
- REST API with comprehensive endpoints
- MCP server for AI assistant integration
- Direct SQLite access for custom queries
- Report generation with charts and visualizations

## Environment Configuration

Required `.env` variables:
```env
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password
TURSO_DB_PATH=./data/garmin.db
COLLECTION_DAYS=7  # Default data collection period
```

## Dependencies

Core dependencies managed via `pyproject.toml`:
- **Data Collection:** `garminconnect`, `garth`, `libsql-experimental`
- **API Server:** `fastapi`, `uvicorn`
- **Visualization:** `matplotlib`, `seaborn`, `plotly`, `weasyprint`
- **Data Processing:** `pandas`
- **MCP Integration:** `mcp`
- **Utilities:** `schedule`, `python-dotenv`, `rich`

## Data Collection Workflow

1. **Authentication:** `GarminAuthenticator` handles login with MFA support
2. **Database Setup:** Creates schema if needed via `TursoDatabase`
3. **Enhanced Collection:** Collects from 15+ Garmin APIs via `enhanced_collector.py`
4. **Intraday Data:** Extracts high-resolution data arrays via `intraday_collector.py`
5. **FIT Processing:** Downloads and processes GPX/FIT files via `fit_processor.py`
6. **Storage:** All data stored in normalized SQLite schema
7. **Logging:** Comprehensive audit trail in `collection_log` table

## API Rate Limits

- 1.0-1.5 second delays between Garmin API calls
- Intraday heart rate limited to last 3 days (data volume)
- Stress data limited to last 7 days
- Automatic retry logic for transient failures

## MCP Integration

The project includes full MCP server implementation for AI assistant integration:
- Database introspection and querying capabilities
- Natural language query support
- Integration with Claude Code via `claude mcp add garmin-turso`
- See `MCP_GUIDE.md` for complete setup instructions