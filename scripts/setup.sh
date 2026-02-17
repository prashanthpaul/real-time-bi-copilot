#!/bin/bash
# =============================================================================
# Real-Time BI Copilot — Setup Script (Unix/macOS)
# =============================================================================
set -e

echo "========================================="
echo " Real-Time BI Copilot - Setup"
echo "========================================="

# 1. Check Python version
echo ""
echo "[1/7] Checking Python version..."
PYTHON_CMD=""
for cmd in python3.11 python3.12 python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$($cmd --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_CMD="$cmd"
            echo "  Found: $cmd ($($cmd --version))"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "  ERROR: Python 3.11+ required. Please install it first."
    exit 1
fi

# 2. Create virtual environment
echo ""
echo "[2/7] Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "  Created: ./venv"
else
    echo "  Already exists: ./venv"
fi

source venv/bin/activate

# 3. Install dependencies
echo ""
echo "[3/7] Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  Dependencies installed."

# 4. Create .env if not exists
echo ""
echo "[4/7] Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env from template. Edit it with your ANTHROPIC_API_KEY."
else
    echo "  .env already exists."
fi

# 5. Generate sample data
echo ""
echo "[5/7] Generating sample data..."
PYTHONPATH=. python data/sample_data_generator.py

# 6. Verify setup
echo ""
echo "[6/7] Verifying installation..."
PYTHONPATH=. python -c "
import duckdb
con = duckdb.connect('./data/database.duckdb')
tables = con.execute('SHOW TABLES').fetchall()
print(f'  Database OK: {len(tables)} tables found')
for t in tables:
    count = con.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
    print(f'    {t[0]}: {count:,} rows')
con.close()
"

# 7. Done
echo ""
echo "[7/7] Setup complete!"
echo ""
echo "========================================="
echo " Next Steps:"
echo "========================================="
echo " 1. Edit .env with your ANTHROPIC_API_KEY"
echo " 2. Start the dashboard:"
echo "      source venv/bin/activate"
echo "      streamlit run streamlit-app/app.py"
echo " 3. For VS Code MCP integration:"
echo "      Copy vscode-config/mcp.json to .vscode/mcp.json"
echo "========================================="
