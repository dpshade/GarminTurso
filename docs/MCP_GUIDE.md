# GarminTurso MCP Integration Guide

This guide explains how to use the Model Context Protocol (MCP) server with your GarminTurso database to enable AI assistants to query your Garmin health data.

## Prerequisites

1. **Collect Data First**: Run `python main.py` to populate the database with your Garmin Connect data
2. **Install tursodb**: The MCP server requires the Turso CLI
   ```bash
   pip install turso-cli
   ```

## Quick Setup

Run the setup script to configure MCP:

```bash
./setup_mcp.sh
```

## Integration Options

### Option 1: Claude Code (Recommended)

Add the MCP server to Claude Code for seamless integration:

```bash
# From the GarminTurso directory
claude mcp add garmin-turso -- tursodb $(pwd)/data/garmin.db --mcp

# Or with absolute path
claude mcp add garmin-turso -- tursodb /home/user/GarminTurso/data/garmin.db --mcp

# For project-specific setup
claude mcp add garmin-turso --local -- tursodb ./data/garmin.db --mcp
```

After adding, restart Claude Code to activate the connection.

### Option 2: Standalone MCP Server

Start the MCP server manually for use with other AI tools:

```bash
tursodb ./data/garmin.db --mcp
```

The server will run on stdin/stdout, ready to receive JSON-RPC requests.

### Option 3: Programmatic Access

Use the MCP server in your own applications:

```python
import subprocess
import json

# Start MCP server
proc = subprocess.Popen(
    ['tursodb', './data/garmin.db', '--mcp'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Initialize connection
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "python-client", "version": "1.0"}
    }
}

# Send request and get response
proc.stdin.write(json.dumps(init_request) + '\n')
proc.stdin.flush()
response = proc.stdout.readline()
```

## Available MCP Tools

Once connected, the MCP server provides these tools:

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `list_tables` | Show all database tables | "What tables are in my database?" |
| `describe_table` | Show table structure | "Describe the activities table" |
| `execute_query` | Run SELECT queries | "Show my average steps per day this week" |
| `insert_data` | Add new records | "Add a manual activity entry" |
| `update_data` | Modify existing data | "Update my weight entry for today" |
| `delete_data` | Remove records | "Delete activities older than 1 year" |
| `schema_change` | Modify database structure | "Add a notes column to activities" |
| `current_database` | Show database info | "What database am I connected to?" |

## Sample Queries for AI Assistants

Once the MCP server is connected, you can ask natural language questions:

### Health Insights
- "What's my average step count for the last 30 days?"
- "Show me my resting heart rate trend this month"
- "What's my best sleep score this week?"
- "How many calories did I burn yesterday?"

### Activity Analysis
- "List my longest runs in the past month"
- "What's my total distance cycled this year?"
- "Show activities where I burned more than 500 calories"
- "What's my average pace for 5K runs?"

### Sleep Patterns
- "What's my average sleep duration this week?"
- "Show nights where I got less than 6 hours of sleep"
- "What's my REM sleep percentage trend?"
- "When did I have the best sleep quality this month?"

### Body Metrics
- "Show my weight trend over the last 3 months"
- "What's my current BMI?"
- "Display body fat percentage changes"

### Stress & Recovery
- "What times of day do I have highest stress?"
- "Show my body battery patterns"
- "When do I typically have lowest stress levels?"

### Complex Queries
- "Compare my weekday vs weekend step counts"
- "Show correlation between sleep quality and next-day activities"
- "Find days where I had high stress but good sleep"
- "List activities followed by poor recovery"

## Example MCP Interactions

### List Tables
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_tables",
    "arguments": {}
  }
}
```

### Query Daily Stats
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "execute_query",
    "arguments": {
      "query": "SELECT date, total_steps, calories_total, resting_heart_rate, sleep_score FROM daily_stats ORDER BY date DESC LIMIT 7"
    }
  }
}
```

### Analyze Activities
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "execute_query",
    "arguments": {
      "query": "SELECT activity_name, activity_type, distance_meters, duration_seconds, calories, avg_heart_rate FROM activities WHERE activity_type = 'running' ORDER BY start_time_gmt DESC LIMIT 10"
    }
  }
}
```

## Testing the MCP Server

Use the provided test script to verify the MCP server is working:

```bash
./test_mcp.sh
```

This will:
1. Initialize the MCP connection
2. List all tables
3. Describe the daily_stats table
4. Run sample queries
5. Display the results

## Managing Claude Code MCP Servers

```bash
# List all configured MCP servers
claude mcp list

# Get details about the Garmin MCP server
claude mcp get garmin-turso

# Remove the MCP server
claude mcp remove garmin-turso

# Check MCP server status
claude mcp status garmin-turso
```

## Troubleshooting

### Database Not Found
- Ensure you've run `python main.py` first to create and populate the database
- Check the database path in your MCP configuration

### Permission Denied
- Make sure the database file has read permissions
- Check that the MCP server has access to the database directory

### Connection Failed
- Verify tursodb is installed: `which tursodb`
- Check that the database path is absolute when using Claude Code
- Restart Claude Code after adding the MCP server

### Query Errors
- Remember that MCP execute_query only supports SELECT statements
- Use the appropriate tool for modifications (insert_data, update_data, delete_data)
- Check table and column names with list_tables and describe_table first

## Security Notes

- The MCP server runs locally and doesn't expose any network ports
- Database access is controlled by file system permissions
- Consider using read-only access for shared environments
- MCP connections are process-isolated

## Advanced Usage

### Custom Queries Library

Create a file with common queries for easy reference:

```sql
-- queries.sql

-- Weekly Summary
SELECT
    DATE(date, 'weekday 0') as week_start,
    AVG(total_steps) as avg_steps,
    AVG(calories_total) as avg_calories,
    AVG(sleep_score) as avg_sleep_score,
    COUNT(DISTINCT date) as days_with_data
FROM daily_stats
GROUP BY week_start
ORDER BY week_start DESC;

-- Activity Performance Trends
SELECT
    activity_type,
    COUNT(*) as count,
    AVG(distance_meters) as avg_distance,
    AVG(duration_seconds/60.0) as avg_duration_minutes,
    AVG(calories) as avg_calories
FROM activities
GROUP BY activity_type
ORDER BY count DESC;

-- Sleep Quality Analysis
SELECT
    CASE
        WHEN overall_sleep_score >= 80 THEN 'Excellent'
        WHEN overall_sleep_score >= 60 THEN 'Good'
        WHEN overall_sleep_score >= 40 THEN 'Fair'
        ELSE 'Poor'
    END as quality,
    COUNT(*) as nights,
    AVG(deep_sleep_seconds/3600.0) as avg_deep_hours,
    AVG(rem_sleep_seconds/3600.0) as avg_rem_hours
FROM sleep_data
GROUP BY quality;
```

### Batch Processing

Process multiple queries efficiently:

```bash
#!/bin/bash
# batch_query.sh

QUERIES=(
    "SELECT COUNT(*) FROM activities"
    "SELECT AVG(total_steps) FROM daily_stats"
    "SELECT MAX(distance_meters) FROM activities WHERE activity_type='running'"
)

for query in "${QUERIES[@]}"; do
    echo "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\", \"params\": {\"name\": \"execute_query\", \"arguments\": {\"query\": \"$query\"}}}"
done | tursodb ./data/garmin.db --mcp
```

## Next Steps

1. Connect the MCP server to Claude Code
2. Explore your health data with natural language queries
3. Create custom dashboards using the query results
4. Set up automated health reports using the API and MCP together
5. Integrate with other tools in your workflow

The MCP server provides a powerful interface for AI-assisted analysis of your Garmin health data while keeping everything local and under your control.