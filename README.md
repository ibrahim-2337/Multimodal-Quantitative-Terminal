# Multimodal Quantitative Intelligence Terminal

An autonomous multimodal intelligence pipeline that integrates live blockchain events (On-Chain) with technical action (Off-Chain) to synthesize high-alpha trading signals for 19+ crypto assets.

## 🚀 Features

*   **High-Throughput Data Pipeline:** Real-time ingestion and normalization of Ethereum blockchain events using `web3.py` and Alchemy RPC.
*   **Triple Convergence Signal Engine:** Synthesizes on-chain "Whale" anomalies ($1,000+ Exchange Inflows/Outflows) with off-chain Technical Analysis (Bollinger Band breakouts and RSI extremes).
*   **Live Backtesting Framework:** Automated snapshots of entry prices with real-time Win/Loss ratio and ROI calculation over a rolling 15-minute window.
*   **Bloomberg-Style Terminal UI:** Custom Streamlit dashboard with Matrix-dark aesthetics, live KPI cards, and color-coded signal feeds.
*   **High Concurrency Storage:** SQLite WAL (Write-Ahead Logging) implementation for simultaneous multi-process ingestion and analysis.

## 🛠️ Tech Stack

*   **Language:** Python 3.13
*   **Blockchain:** Web3.py, Alchemy RPC
*   **Quantitative Finance:** CCXT (Binance API), Pandas-TA
*   **Machine Learning:** Scikit-Learn (Isolation Forest)
*   **Database:** SQLite (WAL Mode)
*   **Dashboard:** Streamlit, Plotly

## 🏹 "Triple Convergence" Logic

To maintain high precision and reduce noise, the engine requires three concurrent signals:
1.  **Whale Anchor (On-Chain):** Recent exchange inflow/outflow detected for the specific asset.
2.  **Bollinger Stretch (Volatility):** Price touching or exceeding standard deviation bands.
3.  **RSI Extremes (Momentum):** Relative Strength Index below 35 (Oversold) or above 65 (Overbought).

## 📊 Backtesting Metrics

The terminal automatically validates its own performance. A "WIN" is defined as a price move of >0.1% in the predicted direction within 15 minutes of the signal generation.

## ⚙️ Setup & Installation

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/ibrahim-2337/crypto-alpha-terminal.git
    cd crypto-alpha-terminal
    ```
2.  **Environment Variables:** Create a `.env` file with your Alchemy URL:
    ```
    ALCHEMY_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
    ```
3.  **Run the Terminal:**
    ```bash
    bash start_trading_terminal.sh
    ```

---
*Developed by Ibrahim Ahmad | NYU Abu Dhabi*
