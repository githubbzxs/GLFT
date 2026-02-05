# GLFT 做市系统（TUI 版）

本项目实现基于 GLFT 模型的加密货币做市系统，当前形态为：
- FastAPI 后端服务
- 终端交互式 TUI 客户端（不再提供 Web GUI）

## 功能概览
- GLFT 闭式近似解做市报价
- 自动参数回推与规则自适应
- 风控：库存、单笔、杠杆、撤单率
- 订单 / 成交 / 持仓查看
- API Key 管理
- 系统配置维护
- 告警查看与已读标记
- PnL CSV 导出

## 运行环境
- Python 3.12+
- PostgreSQL 14+（生产推荐）或 SQLite（开发可用）

## 快速开始

### 1. 准备数据库
使用 PostgreSQL：

```bash
docker compose up -d
```

如果本机没有 Docker，可使用 SQLite（开发模式）：

```bash
DATABASE_URL=sqlite+aiosqlite:///./glft.db
```

### 2. 安装依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

根据实际环境编辑 `backend/.env`（数据库、GRVT、管理员账号等）。

### 3. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. 启动 TUI

另开一个终端：

```bash
cd backend
python tui.py
```

如后端不在本机 8000，可指定：

```bash
python tui.py --api-url http://<host>:<port>/api
```

## TUI 菜单能力
- 仪表盘
- 订单 / 成交 / 持仓
- 策略参数
- 风控执行（含启动/停止引擎）
- API Key 管理
- 系统配置
- 告警中心
- 导出 PnL CSV

## 安全提示
- 主网密钥请使用最小权限并设置 IP 白名单
- 生产部署请更换更强的 JWT 密钥与主加密密钥

## 目录结构

```text
GLFT/
  backend/   FastAPI 后端 + TUI 客户端
```
