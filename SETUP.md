# Setup Guide

## Prerequisites

- Python 3.11+
- pip
- Git
- Docker (optional)
- VS Code (optional, for MCP agent mode)

## Quick Setup (Automated)

### macOS / Linux
```bash
git clone https://github.com/YOUR_USERNAME/real-time-bi-copilot.git
cd real-time-bi-copilot
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/YOUR_USERNAME/real-time-bi-copilot.git
cd real-time-bi-copilot
.\scripts\setup.ps1
```

## Manual Setup

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Generate Sample Data
```bash
PYTHONPATH=. python data/sample_data_generator.py
```

### 5. Verify Installation
```bash
PYTHONPATH=. python scripts/test_mcp_server.py
```

### 6. Start the Dashboard
```bash
PYTHONPATH=. streamlit run streamlit-app/app.py
```

## VS Code MCP Integration

1. Copy the MCP config:
```bash
mkdir -p .vscode
cp vscode-config/mcp.json .vscode/mcp.json
```

2. Open the project in VS Code
3. Enable agent mode (Copilot → Agent)
4. The MCP server starts automatically

## Docker Setup

```bash
# Generate data first
PYTHONPATH=. python data/sample_data_generator.py

# Build and run
docker compose up --build
```

- Dashboard: http://localhost:8501

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'mcp_server'" | Set `PYTHONPATH=.` before running commands |
| "Database not found" | Run `python data/sample_data_generator.py` |
| "ANTHROPIC_API_KEY not set" | Edit `.env` with your API key |
| "Port 8501 in use" | Change `STREAMLIT_PORT` in `.env` or kill existing process |
| Import errors | Ensure `venv` is activated and dependencies installed |
