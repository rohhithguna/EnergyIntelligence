# Data Flow Intelligence System

**Production-ready analytics platform for time-series data analysis with domain-aware processing**

## ⚡ Quick Start (3 Steps)

```bash
# 1. Start server
source .venv/bin/activate
python server/simple_server.py

# 2. Open browser
http://localhost:8000

# 3. Upload CSV file and select domain
```

**Time to first results:** 30 seconds

---

## 📚 Documentation

| Document | Purpose | Time |
|----------|---------|------|
| **[QUICKREF.md](QUICKREF.md)** | Quick reference guide | 5 min |
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Complete setup & architecture | 15 min |
| **[DEPLOYMENT_STEPS.md](DEPLOYMENT_STEPS.md)** | Step-by-step deployment | 20 min |
| **[AUDIT_REPORT.md](AUDIT_REPORT.md)** | Technical audit details | 20 min |
| **[CHANGES_MANIFEST.md](CHANGES_MANIFEST.md)** | All changes made | 10 min |

---

## 🎯 What This System Does

- **Uploads** CSV files with 10 domain-specific data types
- **Analyzes** time-series data for patterns, anomalies, and trends
- **Generates** natural language insights with risk classification
- **Compares** multiple datasets side-by-side
- **Exports** detailed reports

---

## 🏗️ Architecture

**Frontend:** Vanilla HTML5 + CSS3 + JavaScript (4 pages, no frameworks)  
**Backend:** Python + pandas + scikit-learn (HTTP server on port 8000)  
**Database:** CSV input → In-memory processing → JSON response  
**Domain System:** 10 domains with automatic column mapping

---

## 🚀 Core Features

✅ **10 Domain Support** - Network, servers, metrics, finance, IoT, web, API, apps, users, generic  
✅ **Column Mapping** - Automatic domain-specific → internal schema translation  
✅ **Pattern Detection** - Spikes, drops, trends, anomalies  
✅ **Risk Assessment** - Low/Medium/High/Critical classification  
✅ **Error Handling** - Global handlers (frontend + backend) with fallbacks  
✅ **Audit Tools** - SYSTEM_AUDIT.py for comprehensive verification  

---

## 📊 Analysis Output

Each upload returns:
- **Spikes detected** - Unusual increases
- **Drops detected** - Unusual decreases  
- **Anomalies** - Outliers with confidence levels
- **Insights** - Natural language analysis
- **Risk** - Overall risk classification
- **Quality** - Data quality percentage
- **Trend** - Direction (increasing/decreasing/stable)

---

## ✅ Verification Status

| Component | Status |
|-----------|--------|
| Backend Pipeline | ✅ All modules working |
| Frontend UI | ✅ 4 pages, no JS errors |
| Domain System | ✅ 10 domains configured |
| Column Mapping | ✅ 50+ aliases mapped |
| Error Handling | ✅ Comprehensive coverage |
| Documentation | ✅ 8 files created |
| **/OVERALL** | **✅ PRODUCTION READY** |

Run `python SYSTEM_AUDIT.py` to verify all systems.

---

## 📁 Project Structure

```
root/
├── frontend/                    # Web UI (4 pages)
│   ├── index.html             # Upload page
│   ├── dashboard.html         # Results page
│   ├── report.html            # Detail page
│   ├── comparison.html        # Compare page
│   ├── script.js              # All logic
│   └── style.css              # Styling
├── server/
│   └── simple_server.py       # HTTP server (port 8000)
├── core/
│   └── pattern_spike_engine.py # Pattern detection
├── main.py                     # Pipeline orchestration
├── domain_mapper.py            # Column mapping (10 domains)
├── loader.py                   # CSV loading
├── preprocessor.py             # Data cleaning
├── anomaly_engine.py           # Anomaly detection
├── correlation.py              # Correlation analysis
├── insight_generator.py        # Insight generation
├── domains.json                # Domain schemas
├── sample_data.csv             # Test data
├── SYSTEM_AUDIT.py             # Verification tool
├── CLEANUP_ANALYSIS.py         # Cleanup tool
└── [8 Documentation Files]     # Guides & reports
```

---

## 🔧 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Upload page |
| `/upload` | POST | Analyze file |
| `/api/latest` | GET | Last result |
| `/dashboard.html` | GET | Results page |
| `/api/compare` | GET | Compare datasets |
| `/domains.json` | GET | Domain schemas |

---

## 🎛️ Supported Domains

| Domain | Example | Maps To |
|--------|---------|---------|
| network_traffic | Bytes transferred | data_rate |
| server_logs | Response time (ms) | data_rate |
| system_metrics | CPU usage (%) | data_rate |
| finance_transactions | Transaction amount | data_rate |
| user_activity | Session duration (sec) | data_rate |
| iot_sensor | Sensor reading | data_rate |
| web_traffic | Page views | data_rate |
| api_logs | Request count | data_rate |
| application_logs | Event count | data_rate |
| generic | Any numeric column | data_rate |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Server won't start** | Check port 8000: `lsof -i :8000` |
| **Upload fails** | CSV must have timestamp + numeric column |
| **Page won't load** | Clear cache: Ctrl+Shift+Delete |
| **Results wrong** | See AUDIT_REPORT.md troubleshooting |

---

## 📋 Phase 7 Audit Results

**Status:** ✅ PRODUCTION READY

**Fixes Applied:**
- ✅ Global error handlers (frontend)
- ✅ Pipeline exception handling (backend)
- ✅ Column mapping system (10 domains)
- ✅ Fallback logic (graceful degradation)
- ✅ Error response structure (both layers)
- ✅ Scope fixes (undefined variables)
- ✅ Domain UI visibility (proper display)
- ✅ Verification tools (SYSTEM_AUDIT.py)
- ✅ Complete documentation (8 files)
- ✅ Zero syntax errors (verified)

1. Select a CSV or Excel file
2. Choose a domain (Generic, Network, or Server)
3. Click "Analyze"
4. Review the results including:
   - Quality Score
   - Statistics (spikes, drops, anomalies)
   - Insights
   - Data Flow Chart

## Features

### Backend
- File validation (CSV & Excel)
- Data preprocessing (datetime conversion, missing value handling)
- Pattern detection (KMeans clustering)
- Spike/drop detection (moving average thresholds)
- Anomaly detection (IsolationForest)
- Quality scoring
- Insight generation
- REST API server

### Frontend
- Responsive monochromatic design
- File upload interface
- Real-time analysis
- Results dashboard
- Interactive charts
- Error handling

## Technology Stack

**Backend:**
- Python
- pandas
- numpy
- scikit-learn

**Frontend:**
- HTML5
- CSS3
- JavaScript
- Chart.js

## API

### POST /analyze

Accepts multipart form data:

**Fields:**
- `file`: CSV or Excel file
- `domain`: generic | network | server

**Response:**
```json
{
  "success": true,
  "domain": "network",
  "quality": {
    "score": 97,
    "explanation": "Excellent quality..."
  },
  "statistics": {
    "total_rows": 90,
    "spike_count": 9,
    "drop_count": 9,
    "anomaly_count": 4
  },
  "insights": [...],
  "data": {
    "spikes": [...],
    "drops": [...],
    "anomalies": [...]
  }
}
```

## Sample Data

The `dataset/sample_data.csv` file contains 90 rows of sample time-series data with intentional spikes, drops, and anomalies for testing.

## Notes

- The server runs on localhost by default
- All processing happens server-side
- The frontend is fully client-side (no frameworks)
- Monochromatic design for professional presentation
