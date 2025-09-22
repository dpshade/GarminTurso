# 🚀 GarminTurso

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

Comprehensive Garmin Connect data collection with Turso DB integration. Production-ready system that achieves **80% API success rate** and collects **1,800+ data points** with advanced authentication and **continuous sync capabilities**.

## 🏆 Key Features

- **80% API Success Rate** (20/25 APIs working)
- **1,800+ data points** collected in ~40 seconds
- **Continuous sync mode** with automatic data detection
- **Production-tested authentication** with MFA support
- **Comprehensive data coverage**: Enhanced APIs, Intraday arrays, FIT/GPS data
- **Smart sync**: Only fetches data newer than last successful sync
- **Multiple interfaces**: REST API, MCP integration, direct SQLite access

## ✨ Features

### 🔐 Robust Authentication
- Production-tested `garmin_login()` approach from garmin-grafana
- Improved MFA handling with two-step authentication
- Persistent token management with secure permissions
- Automatic session resumption

### 📊 Comprehensive Data Collection
- **Enhanced APIs**: 15/16 sources working (heart rate, steps, stress, sleep, activities)
- **Intraday Data**: High-resolution timestamped data from API response arrays
- **FIT Processing**: GPS coordinates and activity details from GPX exports
- **Continuous Sync**: Automatic detection and sync of new data
- **Rate-limited**: Safe API calls with proper delays (1-2 second intervals)

### 🗄️ Production Database
- Turso DB integration with SQLite storage
- Comprehensive schema with 10 specialized tables including sync tracking
- FastAPI query interface for data retrieval
- Collection metadata and statistics tracking
- MCP (Model Context Protocol) support for AI integrations

### 🔄 Sync Modes
- **Bulk Mode**: Historical data collection (original behavior)
- **Continuous Sync**: Automatic updates when new data is available
- **Smart Sync**: Only fetches data newer than last successful sync
- **Configurable Intervals**: Customizable sync frequency (default: 5 minutes)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ with UV package manager
- Garmin Connect account with credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/dpshade/GarminTurso.git
cd GarminTurso

# Install dependencies with UV (recommended)
uv sync

# Or with pip
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Garmin credentials
```

### Configuration

Create `.env` file:
```env
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password
TURSO_DB_PATH=./data/garmin.db
COLLECTION_DAYS=7
```

## Usage

### Data Collection Modes

**Bulk Collection (Historical Data)**
```bash
# Default: collect last 7 days
python main.py

# Collect specific number of days
python main.py --mode bulk --days 30
```

**Continuous Sync (Automatic Updates)**
```bash
# Via main.py (sync every 5 minutes)
python main.py --mode sync --sync-interval 300

# Dedicated sync service (recommended for production)
python sync.py --mode continuous --interval 300

# One-time sync check
python sync.py --mode single
```

On first run, if MFA is enabled on your Garmin account, you'll be prompted to enter the code from your authenticator app.

The application will:
1. Authenticate with Garmin Connect (tokens are saved for future use)
2. Create the database schema
3. Collect data based on the selected mode
4. Track sync status for continuous operation

### Query the Database

#### Using the REST API

Start the query API server:

```bash
python query_api.py
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

Example queries:
```bash
# Get 7-day summary statistics
curl http://localhost:8000/stats/summary?days=7

# Get recent activities
curl http://localhost:8000/activities?limit=10

# Get sleep data for the last week
curl http://localhost:8000/sleep?days=7

# Get database information
curl http://localhost:8000/database/info
```

#### Direct SQLite Queries

You can also query the database directly using any SQLite client:

```bash
sqlite3 data/garmin.db

# Example queries:
SELECT date, total_steps, calories_total FROM daily_stats ORDER BY date DESC LIMIT 7;
SELECT activity_name, distance_meters, duration_seconds FROM activities LIMIT 10;
```

## Database Schema

The database contains the following main tables:

- `user_profile` - User information
- `daily_stats` - Daily health metrics and summary statistics
- `activities` - Detailed activity/workout data
- `sleep_data` - Comprehensive sleep tracking
- `body_composition` - Weight and body metrics
- `heart_rate_data` - Intraday heart rate measurements
- `stress_data` - Stress level measurements
- `collection_log` - Data collection audit trail

## Configuration

Environment variables (`.env` file):

- `GARMIN_EMAIL` - Your Garmin Connect email
- `GARMIN_PASSWORD` - Your Garmin Connect password
- `TURSO_DB_PATH` - Path to the SQLite database (default: `./data/garmin.db`)
- `COLLECTION_DAYS` - Number of days to collect on initial run (default: 7)

## Security Notes

- Garmin OAuth tokens are stored locally in `~/.garminconnect/` with restricted permissions (700)
- The `.env` file containing credentials should never be committed to version control
- All data is stored locally - no external services beyond Garmin Connect

## Limitations

- Intraday heart rate data is limited to the last 3 days (due to data volume)
- Stress data is limited to the last 7 days
- Rate limiting is implemented to respect Garmin's API (1-2 second delay between requests)

## MCP Integration (Model Context Protocol)

The database can be accessed via MCP for AI-assisted queries:

### Quick Setup
```bash
# Install tursodb if needed
pip install turso-cli

# Run setup script
./setup_mcp.sh

# Add to Claude Code
claude mcp add garmin-turso -- tursodb $(pwd)/data/garmin.db --mcp
```

### Example AI Queries
Once connected via MCP, you can ask natural language questions:
- "What's my average step count this month?"
- "Show my best sleep scores this week"
- "List activities where I burned over 500 calories"
- "Compare weekday vs weekend activity levels"

See `MCP_GUIDE.md` for complete MCP documentation and `example_queries.sql` for SQL query examples.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/dpshade/GarminTurso.git
cd GarminTurso

# Install dependencies
uv sync

# Run tests
python test_final.py
python test_reports.py
```

## 📊 Project Status

- ✅ **Production Ready**: Core functionality stable and tested
- ✅ **80% API Coverage**: 20/25 Garmin APIs working
- ✅ **Continuous Sync**: Automatic data updates
- ✅ **MCP Integration**: AI assistant support
- 🔄 **Active Development**: Regular updates and improvements

## 🐛 Issues and Support

- **Bug Reports**: Please use [GitHub Issues](https://github.com/dpshade/GarminTurso/issues)
- **Feature Requests**: Submit via GitHub Issues with enhancement label
- **Documentation**: See `CLAUDE.md` for developer documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [garminconnect](https://github.com/cyberjunky/python-garminconnect) - Garmin Connect API client
- [garmin-grafana](https://github.com/arpanghosh/garmin-grafana) - Sync mechanism inspiration
- [Turso](https://turso.tech/) - SQLite database platform