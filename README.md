# gpdcodex

可直接运行的 A 股量化交易模拟器示例，基于 [AkShare](https://akshare.akfamily.xyz/) 获取行情，包含回测与简易实时轮询（纯命令行，无图形界面）。额外提供一个独立的 Tkinter 窗口工具，用于批量导出个股资金流（moneyflow_table_gui.py）。

## 环境准备
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 快速开始

运行前可先查看帮助：
```bash
python main.py -h
```

> 说明：本项目是 **命令行工具**，不会弹出窗口或图形界面。执行命令后，终端会输出进度与下单日志；如果没有任何输出，通常是命令参数缺失或网络/依赖问题，参见下方故障排查。

### 1) 分钟级回测
```bash
python main.py backtest 600000 20240101 20240131 --period 5m
```
如果 AkShare 无法返回数据（网络或代码/时间范围问题），程序会提示；成功时会输出成交记录 CSV，并打印最终权益。

### 2) 实时轮询模拟
```bash
python main.py realtime 600000 000001 --interval 60
```
每隔 60 秒拉取快照，基于策略自动发出买卖（T+1 限制）。
运行时会在控制台打印最新权益和买卖指令，例如：
```
Starting realtime engine... Press Ctrl+C to stop.
[2024-01-10 10:00:00] Equity: 1000000.00
BUY 600000 500 @ 10.23
```

### 3) 缓存行情到本地
```bash
python main.py cache 600000 20240101 20240131 --period 5m --out data.parquet
```

### 4) 资金流导出 GUI（可选）

`moneyflow_table_gui.py` 是一个单独的 Tkinter 窗口工具，输入股票代码即可生成最近 1/3/5/10/20 日的主力净流入（亿元）表格并导出为 Excel。

```bash
python moneyflow_table_gui.py
```

提示：
- 默认禁用环境代理，避免请求被代理拦截；如果需要自定义代理，请自行修改脚本开头的环境变量处理。
- 首次运行会安装 Tkinter 依赖，Windows/macOS 自带；Linux 服务器如无图形环境则无法弹窗。

## 代码结构
- `quant_simulator/data_loader.py`: 行情获取与缓存。
- `quant_simulator/broker.py`: 账户、持仓、T+1 处理。
- `quant_simulator/strategy.py`: 拉升识别 + 止盈止损策略。
- `quant_simulator/backtest.py`: 分钟级回测驱动。
- `quant_simulator/realtime.py`: 实时轮询引擎。
- `main.py`: CLI 入口。

> 说明：AkShare 需联网获取数据；如果在受限网络下运行，请预先在有网络的环境缓存数据再离线使用。

## 常见问题

- **运行 `python main.py` 没反应？** 需要带子命令（`backtest`/`realtime`/`cache`），否则 argparse 会直接打印帮助并退出。
- **AkShare 未安装或网络受限？** 请先在联网环境执行 `pip install -r requirements.txt`，并确认可以访问 AkShare 数据接口。
- **实时模式无输出？** 可能是快照数据为空（网络或代码不在沪深 A 股范围），终端会提示；请更换可交易的 A 股代码并检查网络。
