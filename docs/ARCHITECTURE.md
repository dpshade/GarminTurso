# GarminTurso Architecture

## Current Architecture (Multi-Component)

GarminTurso is currently designed as **multiple independent components** that can run separately:

### 🗂️ **Clean File Structure**

```
GarminTurso/
├── 📁 src/                    # Core library modules
│   ├── 📁 core/              # Essential functionality
│   │   ├── auth.py           # Authentication handling
│   │   ├── database.py       # Database operations
│   │   └── sync_service.py   # Continuous sync logic
│   ├── 📁 collectors/        # Data collection modules
│   │   ├── garmin_collector.py      # Main production collector
│   │   ├── enhanced_collector.py    # Enhanced API collection
│   │   ├── intraday_collector.py    # High-res timestamped data
│   │   └── fit_processor.py         # GPS/FIT file processing
│   └── 📁 utils/             # Utility modules
│       ├── data_processor.py        # Data transformation
│       ├── report_generator.py      # Report generation
│       └── 📁 charts/              # Chart generation
├── 📁 scripts/               # Standalone services
│   ├── sync.py              # Continuous sync service
│   ├── query_api.py         # REST API server (FastAPI)
│   ├── mcp_server.py        # MCP server for AI integration
│   ├── generate_report.py   # Report generation utility
│   └── setup_mcp.sh         # MCP setup script
├── 📁 tests/                # Test suite
├── 📁 docs/                 # Documentation
├── 📁 templates/            # HTML templates
└── main.py                  # Primary entry point
```

### 🔧 **Component Architecture**

#### **1. Data Collection Layer**
- **`main.py`**: Primary entry point for bulk/sync collection
- **`scripts/sync.py`**: Dedicated continuous sync daemon
- **`src/collectors/`**: Specialized data collectors

#### **2. Storage Layer**
- **`src/core/database.py`**: SQLite/Turso database operations
- **10 specialized tables** with sync tracking

#### **3. API Layer**
- **`scripts/query_api.py`**: REST API (FastAPI) with 25+ endpoints
- **`scripts/mcp_server.py`**: MCP server for AI integrations

#### **4. Utility Layer**
- **`src/utils/`**: Report generation, data processing, charts

## Architecture Options

### **Option A: Current Multi-Component (Recommended)**

**✅ Advantages:**
- **Flexibility**: Run only needed components
- **Scalability**: Scale components independently
- **Maintenance**: Easier to debug and update individual parts
- **Resource Efficiency**: Only use what you need

**Example Usage:**
```bash
# Data collection only
python main.py --mode bulk --days 30

# Continuous sync daemon
python scripts/sync.py --mode continuous

# API server only
python scripts/query_api.py

# MCP server only
python scripts/mcp_server.py
```

### **Option B: Single Unified Server**

If you prefer a **single server/package**, we could consolidate into:

```python
# Unified server approach
python garmin_turso.py --services api,sync,mcp --port 8000
```

**🔄 Would Include:**
- Single entry point with service selection
- Combined FastAPI app with multiple routers
- Background sync tasks
- Integrated MCP endpoints
- Unified configuration

## Current Benefits of Multi-Component Design

### **🎯 Production Flexibility**
- **Development**: Run sync service on developer machine
- **Server**: Run API service on production server
- **AI Integration**: Run MCP server for Claude/AI access
- **Reporting**: Generate reports on-demand

### **📊 Resource Management**
- **Memory**: Only load needed modules
- **CPU**: Dedicated processes for intensive tasks
- **Network**: API server separate from data collection

### **🔧 Operational Advantages**
- **Monitoring**: Monitor each service independently
- **Deployment**: Deploy components to different environments
- **Updates**: Update individual components without affecting others
- **Debugging**: Isolate issues to specific components

## Recommendations

### **For Most Users: Keep Multi-Component**
The current architecture is **production-ready** and provides maximum flexibility.

### **For Simplified Deployment: Consider Consolidation**
If you want a single deployable package, we can create a unified server while keeping the modular components available.

### **Hybrid Approach**
- Keep current modular design
- Add optional unified entry point: `python server.py --all`
- Best of both worlds

## Technical Implementation

The reorganized structure maintains **clean separation of concerns**:

- **`src/core/`**: Authentication, database, sync logic
- **`src/collectors/`**: Data collection specialists
- **`src/utils/`**: Supporting utilities
- **`scripts/`**: Standalone services
- **`tests/`**: Comprehensive testing

All modules use **proper imports** and can be used independently or together.

---

**Question**: Would you like to consolidate into a single server, or keep the flexible multi-component architecture?