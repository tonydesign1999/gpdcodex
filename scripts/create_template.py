from pathlib import Path

import pandas as pd


def main():
    path = Path("data/templates/order_import_template.xlsx")
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {"编码": "SKU001", "名称": "测试产品A", "店铺": "广州天河店", "数量": 10},
        {"编码": "SKU002", "名称": "测试产品B", "店铺": "广州天河店", "数量": 4},
    ])
    df.to_excel(path, index=False)
    print(f"模板已生成: {path}")


if __name__ == "__main__":
    main()
