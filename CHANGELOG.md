# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation for GitHub
- Comprehensive GitHub repository setup
- GitHub Actions CI/CD workflows
- Issue and PR templates

## [1.0.0] - 2024-XX-XX

### Added
- Production-ready Garmin Connect data collection
- 80% API success rate (20/25 APIs working)
- Comprehensive authentication with MFA support
- Enhanced API data collection (15/16 endpoints)
- Intraday data extraction with high-resolution timestamps
- FIT file processing for GPS coordinates and activity details
- Turso DB integration with SQLite storage
- FastAPI query interface with 25+ endpoints
- MCP (Model Context Protocol) server for AI integrations
- **Continuous sync mode** with automatic data detection
- **Smart sync** - only fetches data newer than last successful sync
- Configurable sync intervals (default: 5 minutes)
- Rate limiting to respect Garmin's API (1-2 second delays)
- Comprehensive database schema with 10 specialized tables
- Production-tested authentication using garmin_login() approach
- Robust error handling and detailed logging
- Report generation with charts and visualizations
- Multiple access methods: REST API, MCP, direct SQLite

### Database Schema
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

### Features
- **Bulk Mode**: Historical data collection (original behavior)
- **Continuous Sync**: Automatic updates when new data is available
- **Single Sync**: One-time sync check for testing
- **Authentication**: Production-tested with MFA support
- **Data Collection**: 1,800+ data points in ~40 seconds
- **Rate Limiting**: Respectful API usage with proper delays
- **Multiple Interfaces**: REST API, MCP integration, direct access

### Security
- Garmin OAuth tokens stored locally with restricted permissions
- Environment-based configuration
- No external services beyond Garmin Connect
- All data stored locally

### Documentation
- Comprehensive README with badges and usage examples
- Developer documentation in CLAUDE.md
- MCP integration guide
- Example SQL queries
- Contributing guidelines
- Security considerations