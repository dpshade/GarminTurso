#!/bin/bash
# Setup script for GarminTurso MCP (Model Context Protocol) integration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 GarminTurso MCP Setup${NC}"
echo ""

# Check if tursodb is installed
if ! command -v tursodb &> /dev/null; then
    echo -e "${YELLOW}⚠️  tursodb is not installed${NC}"
    echo "Installing tursodb..."

    # Install tursodb via pip
    pip install turso-cli

    if command -v tursodb &> /dev/null; then
        echo -e "${GREEN}✅ tursodb installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install tursodb${NC}"
        echo "Please install manually: pip install turso-cli"
        exit 1
    fi
else
    echo -e "${GREEN}✅ tursodb is already installed${NC}"
fi

# Check if database exists
DB_PATH="./data/garmin.db"

if [ ! -f "$DB_PATH" ]; then
    echo -e "${YELLOW}⚠️  Database not found at $DB_PATH${NC}"
    echo "Run 'python main.py' first to collect data from Garmin Connect"
    exit 1
fi

echo -e "${GREEN}✅ Found database at $DB_PATH${NC}"

# Display MCP setup instructions
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}MCP Server Setup Instructions${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Option 1: Claude Code
echo -e "${GREEN}Option 1: Claude Code Integration${NC}"
echo "Add the MCP server to Claude Code with:"
echo ""
echo -e "${YELLOW}claude mcp add garmin-turso -- tursodb $(pwd)/data/garmin.db --mcp${NC}"
echo ""
echo "Then restart Claude Code to activate the connection."
echo ""

# Option 2: Standalone MCP Server
echo -e "${GREEN}Option 2: Standalone MCP Server${NC}"
echo "Start the MCP server manually with:"
echo ""
echo -e "${YELLOW}tursodb $DB_PATH --mcp${NC}"
echo ""

# Option 3: Test MCP Server
echo -e "${GREEN}Option 3: Test MCP Server${NC}"
echo "Test the MCP server with sample queries:"
echo ""
echo -e "${YELLOW}./test_mcp.sh${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Ask if user wants to generate test script
read -p "Would you like to generate a test script for the MCP server? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > test_mcp.sh << 'EOF'
#!/bin/bash
# Test script for GarminTurso MCP server

DB_PATH="./data/garmin.db"

echo "Testing MCP server with sample queries..."
echo ""

cat << 'JSON' | tursodb $DB_PATH --mcp
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_tables", "arguments": {}}}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "describe_table", "arguments": {"table": "daily_stats"}}}
{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "execute_query", "arguments": {"query": "SELECT date, total_steps, calories_total, sleep_score FROM daily_stats ORDER BY date DESC LIMIT 5"}}}
{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "execute_query", "arguments": {"query": "SELECT COUNT(*) as total_activities, AVG(distance_meters) as avg_distance FROM activities"}}}
JSON
EOF

    chmod +x test_mcp.sh
    echo -e "${GREEN}✅ Created test_mcp.sh${NC}"
fi

echo ""
echo -e "${GREEN}✨ MCP setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Add the MCP server to Claude Code (recommended)"
echo "2. Test queries with AI assistants"
echo "3. Explore your Garmin data interactively"