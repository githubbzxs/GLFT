# GLFT 终端客户端（纯 TUI）

本项目当前仅保留一个终端交互客户端，不再包含本地后端服务与 Web 前端。

## 功能概览
- 登录远程 API
- 仪表盘查看
- 订单 / 成交 / 持仓查看
- 策略参数查看与更新
- 风控状态查看、阈值更新、引擎启停
- API Key 管理
- 系统配置管理
- 告警查看与已读标记
- PnL CSV 导出

## 运行环境
- Python 3.12+

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 启动客户端

```bash
python tui.py
```

默认访问 `http://127.0.0.1:8000/api`。  
如果远程 API 地址不同，请显式传入：

```bash
python tui.py --api-url http://<host>:<port>/api
```

## 注意事项
- 当前仓库不再提供后端服务实现。
- 你需要有一个可用的兼容 API 服务地址。
- Windows 终端如出现中文乱码，可先执行：`chcp 65001`

## 目录结构

```text
GLFT/
  tui.py
  requirements.txt
```
