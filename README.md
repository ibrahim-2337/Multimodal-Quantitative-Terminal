# Multimodal Quantitative Terminal

A real-time trading terminal that correlates on-chain "whale" moves with technical price action. It monitors Ethereum events and Binance markets to find high-conviction entries across 19+ crypto assets.

## Core Features
*   **Whale Tracking**: Ingests live Ethereum events via `web3.py` and Alchemy to find large-scale inflows and outflows.
*   **Signal Engine**: Combines on-chain anomalies with technical indicators (Bollinger Bands, RSI) to generate trades.
*   **Live Dashboard**: A Streamlit-based UI for real-time monitoring of signals, whale movements, and backtest results.
*   **Backtesting**: Automatically tracks entry prices and calculates a rolling Win/Loss ratio over 15-minute windows.
*   **WAL Storage**: Uses SQLite in Write-Ahead Logging mode for safe, simultaneous data ingestion and dashboard reading.

## The Signal Logic
To reduce noise, the terminal only fires a signal if three things align:
1.  **Whale Move**: Significant on-chain transfer detected within the last 15 minutes.
2.  **Bollinger Stretch**: Price is touching or breaking outside the 2-std bands.
3.  **RSI Extreme**: Relative Strength Index is <35 (Oversold) or >65 (Overbought).

## How to Run
1.  **Setup**:
    ```bash
    git clone https://github.com/ibrahim-2337/Multimodal-Quantitative-Terminal.git
    cd Multimodal-Quantitative-Terminal
    ```
2.  **Keys**: Create a `.env` file with your `ALCHEMY_URL`.
3.  **Start Terminal**:
    ```bash
    bash start_trading_terminal.sh
    ```

## Notes
- **WebSockets**: The engine uses Binance's public WebSocket feeds for 1-second price ticks.
- **Statistical Whales**: Thresholds for "Whale" moves are calculated dynamically using a 2-std deviation from the mean per token, rather than a hardcoded dollar amount.

---
*Developed by Ibrahim Ahmad | NYU Abu Dhabi*
