#!/bin/bash

# 1. Kill everything old
pkill -f "python3 ingestion.py"
pkill -f "python3 signal_engine.py"
pkill -f "streamlit"
rm -f "whale_tracker.db"*

# 2. Start the Terminal
echo "🚀 Starting AI Trading Terminal..."
source venv/bin/activate

echo "🐋 Starting Whale Ingestion Engine..."
python3 ingestion.py > ingestion.log 2>&1 &

echo "🤖 Starting AI Signal Engine..."
python3 signal_engine.py > signal_engine.log 2>&1 &

echo "📈 Launching Alpha Dashboard..."
streamlit run dashboard.py --server.port 8501

echo "✅ All processes running!"
