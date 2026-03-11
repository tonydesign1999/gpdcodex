# 局域网本地库存与发货管理系统（FastAPI 版）

> 第一版：Python + FastAPI + SQLAlchemy + SQLite，本地文件存储，支持局域网访问。

## 1. 功能范围
- 基础资料管理：产品、店铺
- 入库扫码、库存汇总/流水、库存调整
- Excel 订单导入（兼容中文表头：编码、名称、店铺、数量）
- 订单锁库（事务一致性）
- 自动拆箱并生成装箱单
- 发货流程（开始扫码、扫商品、绑顺丰单号、确认发货）
- Excel 导出（库存、发货、客户维度）
- 装箱单打印页面（HTML，可浏览器直接打印）

## 2. 项目结构

```text
app/
  main.py
  core/
  db/
  models/
  schemas/
  routers/
  services/
  utils/
scripts/
tests/
requirements.txt
README.md
```

## 3. 安装与启动（Windows / 局域网）

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_data.py
python scripts/create_template.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

局域网设备可通过 `http://服务器IP:8000/docs` 访问 Swagger 文档并调试接口。

## 4. 默认示例账号
- 用户名：`admin`
- 密码：`admin123`

## 5. API 概览
- 认证：`/api/auth/login` `/api/auth/logout`
- 产品：`/api/products`
- 店铺：`/api/shops`
- 库存：`/api/inventory/*`
- 订单：`/api/orders/*`
- 装箱单：`/api/packing-orders/*`
- 发货：`/api/shipment/*`
- 导出：`/api/export/*`

## 6. 统一响应格式
成功：
```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```
失败：
```json
{
  "success": false,
  "message": "顺丰单号重复",
  "error_code": "SF_DUPLICATE"
}
```

## 7. SQLite 与后续迁移
当前数据库地址：`sqlite:///./data/inventory.db`（见 `app/core/config.py`）。
后续切换 PostgreSQL 仅需修改连接串并引入迁移工具（建议 Alembic）。

## 8. 订单导入模板
执行 `python scripts/create_template.py` 后可得到：
`data/templates/order_import_template.xlsx`

## 9. 注意事项
- 第一版未接入真实打印机驱动，打印通过 `/api/packing-orders/{packing_no}/print` 返回 HTML 页面。
- 第一版登录 token 采用内存存储，服务重启会失效，适合局域网 MVP。
