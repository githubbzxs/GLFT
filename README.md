# GLFT 做市系统（GRVT 主网）

本项目实现基于 GLFT 模型的加密货币交易所做市量化系统，含 Web GUI、风控、告警、报表与参数自动调优。当前默认对接 GRVT 主网 BTC 永续。

## 功能概览
- GLFT 闭式近似解做市报价
- 自动参数回推与规则自适应
- 风控：库存、单笔、杠杆、撤单率、熔断
- 订单/成交/持仓监控
- 报表导出（CSV）
- 告警：页面 + 邮件

## 运行环境
- Python 3.12+
- Node.js 18+
- PostgreSQL 14+

## 快速开始

### 1. 准备数据库
可自行安装 PostgreSQL，或使用 docker-compose：

```bash
docker compose up -d
```

如果本机没有 Docker，可改用 SQLite（开发模式）：

```bash
DATABASE_URL=sqlite+aiosqlite:///./glft.db
```

### 2. 后端
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

编辑 `.env`，配置数据库与 GRVT 主网密钥等参数。

启动后端：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端
```bash
cd frontend
npm install
npm run dev
```

浏览器访问：`http://localhost:5173`

## 安全提示
- 主网密钥请使用最小权限并设置 IP 白名单
- 生产部署请更换更强的 JWT 密钥与主加密密钥

## 目录结构
```
GLFT/
  backend/   FastAPI 后端
  frontend/  React 前端
```
