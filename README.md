# Binance 永续合约高位开空监控器

一个面向 Binance USDⓈ-M 永续合约的监控 MVP：自动扫描涨幅榜 Top N 与手动自选交易对，计算过热评分、信号等级、交易计划参考，并提供 Web Dashboard、REST API、SQLite 落库和 Telegram 告警。

> 当前版本只做监控、评分、预警和复盘数据记录，不自动下单。

## 功能

- 扫描 U 本位永续合约 24h 涨幅榜。
- 支持 `MANUAL_SYMBOLS` 自选交易对。
- 拉取 5m、15m、1h K 线，以及 Funding、Open Interest。
- 计算 EMA、RSI、ATR、成交量 Z-score、涨幅、OI 变化。
- 生成 0-100 高位开空评分和 Level 0-4 信号。
- 为 Level 3 输出入场、止损、止盈参考。
- Dashboard：`/`。
- API：`/api/snapshots`、`/api/signals`、`/api/scan/run`、`/api/backtest/summary`。
- Telegram 告警去重。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

打开：<http://localhost:8000>

## Docker 部署

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f monitor
```

## 配置

| 变量 | 默认值 | 说明 |
|---|---:|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/monitor.db` | 数据库连接 |
| `BINANCE_FAPI_BASE_URL` | `https://fapi.binance.com` | Binance USD-M Futures REST 地址 |
| `SCAN_INTERVAL_SECONDS` | `30` | 扫描间隔 |
| `TOP_N` | `10` | 涨幅榜数量 |
| `MANUAL_SYMBOLS` | 空 | 逗号分隔自选交易对 |
| `MIN_QUOTE_VOLUME_24H` | `50000000` | 最低 24h 成交额过滤 |
| `TELEGRAM_BOT_TOKEN` | 空 | Telegram Bot token |
| `TELEGRAM_CHAT_ID` | 空 | Telegram chat id |

## 信号等级

- Level 0：正常或仅观察。
- Level 1：短线过热。
- Level 2：做空观察，等待结构确认。
- Level 3：候选开空，必须同时有高分与假突破/支撑破位等结构确认。
- Level 4：预留给禁止做空 / 强趋势风险过高。

## 复盘接口

`/api/backtest/summary` 会把历史 Level 3 信号与后续快照做简化匹配，输出信号后的 MFE/MAE，用于第一阶段复盘。它不是完整撮合回测，但可以快速判断信号是否有统计优势。


## VPS 代理配置

如果 VPS 访问 Binance 或 Telegram 不稳定，可以在 `.env` 里加入出站代理：

```env
HTTP_PROXY=http://你的代理地址:端口
HTTPS_PROXY=http://你的代理地址:端口
NO_PROXY=localhost,127.0.0.1
```

Docker Compose 会通过 `env_file: .env` 把这些变量传入容器，HTTP 客户端会自动读取标准代理环境变量。
