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

### 2) 实时轮询模拟（可交互输入股票）
```bash
# 直接在命令后输入股票代码
python main.py realtime 600000 000001 --interval 60

# 或不带代码，程序会提示你输入，例如：600519 000001
python main.py realtime
```
启动后会先打印当前策略的中文说明，然后每隔 60 秒拉取快照，基于策略自动发出买卖（T+1 限制）。
实时跟踪信息会在终端滚动输出，例如：
```
当前量化策略（中文说明）：
- 监控目标股票的分钟级最新价与成交额，寻找短时间拉升。
- 条件：最近配置窗口（默认5根）内的复合涨幅超过阈值（默认1.5%），且成交额均值/更长窗口均值大于放量倍数（默认1.5倍）。
- 满足条件时买入固定手数（默认每次500股）。
- 若持仓浮盈达到止盈线（默认+1%）或浮亏触及止损线（默认-0.5%），则卖出全部持仓。
- 所有买入遵守T+1约束：当日买入的数量冻结，次日才能卖出。
- 模拟交易包含滑点与手续费，用于更加接近真实成交。
Starting realtime engine... Press Ctrl+C to stop.
[2024-01-10 10:00:00.123456] 跟踪 600000 现价 10.23 | 短期涨幅 1.60% | 放量倍数 1.80 | 信号: buy 数量 500
下单买入 600000 数量 500 价格 10.23？ [y/N]: y
BUY 600000 500 @ 10.23
[2024-01-10 10:00:00.123456] Equity: 1001023.00
```
> 提示：默认每次买卖前会询问是否确认下单（输入 `y`/`yes`/`是`/`好` 才会执行）。

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
