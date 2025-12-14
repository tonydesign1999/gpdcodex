# gpdcodex

可直接运行的 A 股量化交易模拟器示例，基于 [AkShare](https://akshare.akfamily.xyz/) 获取行情，包含回测与简易实时轮询。

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

### 3) 缓存行情到本地
```bash
python main.py cache 600000 20240101 20240131 --period 5m --out data.parquet
```

## 代码结构
- `quant_simulator/data_loader.py`: 行情获取与缓存。
- `quant_simulator/broker.py`: 账户、持仓、T+1 处理。
- `quant_simulator/strategy.py`: 拉升识别 + 止盈止损策略。
- `quant_simulator/backtest.py`: 分钟级回测驱动。
- `quant_simulator/realtime.py`: 实时轮询引擎。
- `main.py`: CLI 入口。

> 说明：AkShare 需联网获取数据；如果在受限网络下运行，请预先在有网络的环境缓存数据再离线使用。
