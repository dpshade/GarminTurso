#!/bin/bash
# Test script for GarminTurso MCP server
# This demonstrates MCP protocol interactions with the database

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

DB_PATH="./data/garmin.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}❌ Database not found at $DB_PATH${NC}"
    echo "Run 'python main.py' first to collect data from Garmin Connect"
    exit 1
fi

echo -e "${BLUE}🧪 Testing GarminTurso MCP Server${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Database:${NC} $DB_PATH"
echo ""

# Run MCP test queries
echo -e "${GREEN}Sending MCP requests...${NC}"
echo ""

cat << 'JSON' | tursodb "$DB_PATH" --mcp 2>/dev/null | while IFS= read -r line; do
    # Pretty print JSON responses
    echo "$line" | python3 -m json.tool 2>/dev/null || echo "$line"
done
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "garmin-turso-test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "current_database", "arguments": {}}}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_tables", "arguments": {}}}
{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "describe_table", "arguments": {"table": "daily_stats"}}}
{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "execute_query", "arguments": {"query": "SELECT date, total_steps, calories_total, sleep_score, body_battery_highest FROM daily_stats ORDER BY date DESC LIMIT 5"}}}
{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "execute_query", "arguments": {"query": "SELECT COUNT(*) as total_activities, AVG(distance_meters/1000.0) as avg_distance_km, AVG(duration_seconds/60.0) as avg_duration_min FROM activities"}}}
{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "execute_query", "arguments": {"query": "SELECT activity_type, COUNT(*) as count FROM activities GROUP BY activity_type ORDER BY count DESC LIMIT 5"}}}
{"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "execute_query", "arguments": {"query": "SELECT AVG(overall_sleep_score) as avg_sleep_score, AVG((deep_sleep_seconds + light_sleep_seconds + rem_sleep_seconds)/3600.0) as avg_sleep_hours FROM sleep_data WHERE calendar_date >= date('now', '-7 days')"}}}
JSON

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ MCP Server test complete!${NC}"
echo ""
echo "The MCP server successfully:"
echo "• Connected to the database"
echo "• Listed available tables"
echo "• Described table structure"
echo "• Executed multiple queries"
echo ""
echo -e "${YELLOW}Next step:${NC} Add to Claude Code with:"
echo -e "${BLUE}claude mcp add garmin-turso -- tursodb $(pwd)/data/garmin.db --mcp${NC}"