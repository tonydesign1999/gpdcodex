# moneyflow_table_gui.py
# ========= 0. 禁用代理 & 禁用 requests 环境代理 =========
import os
import requests
import requests.utils as ru

print("初始化：清理代理设置...")

for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    v = os.environ.pop(k, None)
    print(k, "=", v)

os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"


def _no_env_proxies(url, no_proxy=None):
    # 无论系统环境如何，这里一律不返回代理设置
    return {}


ru.get_environ_proxies = _no_env_proxies

print("已禁用 requests 环境代理读取。")

# ========= 1. 导入第三方库 =========
import akshare as ak
import pandas as pd
from datetime import datetime

# Tkinter 图形界面
import tkinter as tk
from tkinter import messagebox, scrolledtext


# ========= 2. 资金流计算逻辑 =========
WINDOWS = [1, 3, 5, 10, 20]


def get_moneyflow_window_sum(stock: str, market: str, window: int) -> float:
    """
    用 AkShare 从东方财富取个股资金流数据，
    计算最近 window 个交易日的【主力净流入-净额】之和，单位转成“亿元”。
    """
    print(f"获取资金流: {stock}.{market} 最近 {window} 日...")
    df = ak.stock_individual_fund_flow(stock=stock, market=market)

    if df is None or df.empty:
        print(f"  ⚠ {stock}.{market} 无数据")
        return float("nan")

    # 日期转成时间类型，排序
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期")

    recent = df.tail(window)

    if "主力净流入-净额" not in recent.columns:
        print(f"  ⚠ 数据列中没有 '主力净流入-净额'，现有列：{recent.columns}")
        return float("nan")

    # 元 -> 亿
    total_e = recent["主力净流入-净额"].sum() / 1e8
    return round(total_e, 2)


def build_table(stock_dict) -> pd.DataFrame:
    """
    stock_dict: { 显示名称: (code, market) }
    """
    rows = []
    for name, (code, market) in stock_dict.items():
        row = {"名称": name, "代码": code, "市场": market}
        for w in WINDOWS:
            col_name = f"{w}日主力净流入E"
            value = get_moneyflow_window_sum(code, market, w)
            row[col_name] = value
        rows.append(row)

    df_out = pd.DataFrame(rows)
    cols = ["名称", "代码", "市场"] + [f"{w}日主力净流入E" for w in WINDOWS]
    df_out = df_out[cols]
    return df_out


# ========= 3. 解析用户输入的股票代码 =========
def parse_stock_input(text: str):
    """
    支持输入格式：
    - 000001.sz
    - 600519.sh
    - 000001  （自动识别 sz）
    - 600519  （自动识别 sh）
    多个代码可用换行或逗号分隔。
    返回: { 显示名称: (code, market) }
    """
    # 按换行和逗号拆分
    raw_items = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.replace("，", ",").split(",") if p.strip()]
        raw_items.extend(parts)

    stocks = {}
    for item in raw_items:
        if not item:
            continue

        token = item.lower()
        code = ""
        market = ""

        if "." in token:
            # 形如 000001.sz
            parts = token.split(".")
            if len(parts) != 2:
                raise ValueError(f"股票代码格式有误: {item}")
            code = parts[0]
            market = parts[1]
            if market not in ("sh", "sz"):
                raise ValueError(f"无法识别市场（只能是 sh 或 sz）: {item}")
        else:
            # 只有数字：自动判断
            code = token
            if not code.isdigit() or len(code) != 6:
                raise ValueError(f"股票代码格式有误（需6位数字）: {item}")
            if code.startswith(("0", "3")):
                market = "sz"
            elif code.startswith("6"):
                market = "sh"
            else:
                raise ValueError(f"无法自动判断市场，请改为 代码.市场 格式，如 000001.sz: {item}")

        display_name = f"{code}.{market}"
        stocks[display_name] = (code, market)

    if not stocks:
        raise ValueError("没有解析到任何有效股票代码")

    return stocks


# ========= 4. 图形界面逻辑 =========
def on_generate():
    text = input_box.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("提示", "请先输入股票代码！")
        return

    try:
        stock_dict = parse_stock_input(text)
    except Exception as e:
        messagebox.showerror("输入错误", str(e))
        return

    try:
        df = build_table(stock_dict)
    except Exception as e:
        messagebox.showerror("运行错误", f"获取资金流数据时出错：\n{e}")
        return

    # 根据日期生成文件名
    today_str = datetime.now().strftime("%Y%m%d")
    out_file = f"moneyflow_akshare_{today_str}.xlsx"
    try:
        df.to_excel(out_file, index=False)
    except Exception as e:
        messagebox.showerror("保存失败", f"保存 Excel 时出错：\n{e}")
        return

    messagebox.showinfo("完成", f"已生成资金流 Excel 文件：\n{out_file}")


def main():
    root = tk.Tk()
    root.title("资金流导出工具（AkShare + 东方财富）")

    # 窗口大小
    root.geometry("520x380")

    label = tk.Label(
        root,
        text="请输入股票代码（每行一个，支持 000001 / 000001.sz / 600519.sh）：",
        anchor="w",
        justify="left",
    )
    label.pack(padx=10, pady=10, anchor="w")

    global input_box
    input_box = scrolledtext.ScrolledText(root, width=60, height=12)
    input_box.pack(padx=10, pady=5)

    # 默认示例
    input_box.insert(tk.END, "000001\n000651\n600519.sh")

    btn = tk.Button(root, text="生成资金流 Excel", command=on_generate)
    btn.pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    main()
