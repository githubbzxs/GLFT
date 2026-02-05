from __future__ import annotations

import argparse
import getpass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GlftApiClient:
    def __init__(self, base_url: str, timeout: float = 20.0) -> None:
        normalized_base_url = base_url.rstrip("/")
        self._http = httpx.Client(base_url=normalized_base_url, timeout=timeout)
        self._token: str | None = None

    def close(self) -> None:
        self._http.close()

    def clear_token(self) -> None:
        self._token = None

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        auth_required: bool = True,
    ) -> Any:
        headers: dict[str, str] = {}
        if auth_required:
            if not self._token:
                raise ApiError("当前未登录，请先登录。", status_code=401)
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            response = self._http.request(method=method, url=path, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ApiError(f"网络请求失败：{exc}") from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                data = response.json()
                if isinstance(data, dict) and "detail" in data:
                    detail = str(data["detail"])
            except Exception:
                detail = response.text
            raise ApiError(detail, status_code=response.status_code)

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def login(self, username: str, password: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/auth/login",
            payload={"username": username, "password": password},
            auth_required=False,
        )
        self._token = result["access_token"]
        return result

    def get_me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    def get_dashboard_metrics(self) -> dict[str, Any]:
        return self._request("GET", "/dashboard/metrics")

    def get_orders(self) -> list[dict[str, Any]]:
        return self._request("GET", "/orders")

    def get_trades(self) -> list[dict[str, Any]]:
        return self._request("GET", "/trades")

    def get_positions(self) -> list[dict[str, Any]]:
        return self._request("GET", "/positions")

    def get_strategy_params(self) -> dict[str, Any]:
        return self._request("GET", "/strategy/params")

    def update_strategy_params(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/strategy/params", payload=payload)

    def get_risk_status(self) -> dict[str, Any]:
        return self._request("GET", "/risk/status")

    def get_risk_limits(self) -> dict[str, Any]:
        return self._request("GET", "/risk/limits")

    def update_risk_limits(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/risk/limits", payload=payload)

    def engine_start(self) -> dict[str, Any]:
        return self._request("POST", "/engine/start")

    def engine_stop(self) -> dict[str, Any]:
        return self._request("POST", "/engine/stop")

    def get_keys(self) -> dict[str, Any]:
        return self._request("GET", "/keys")

    def save_keys(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/keys", payload=payload)

    def get_config(self) -> dict[str, Any]:
        return self._request("GET", "/config")

    def update_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/config", payload=payload)

    def get_alerts(self) -> list[dict[str, Any]]:
        return self._request("GET", "/alerts")

    def mark_alert_read(self, alert_id: int) -> dict[str, Any]:
        return self._request("POST", f"/alerts/{alert_id}/read")

    def export_pnl_csv(self) -> str:
        result = self._request("GET", "/reports/pnl.csv")
        if isinstance(result, str):
            return result
        raise ApiError("服务端未返回有效的 CSV 数据。")


class GlftTuiApp:
    def __init__(self, api: GlftApiClient, console: Console) -> None:
        self.api = api
        self.console = console

    def run(self) -> None:
        self.console.print(
            Panel.fit(
                "[bold cyan]GLFT 终端控制台（TUI）[/bold cyan]\n通过键盘菜单完成原 GUI 的全部核心操作。",
                border_style="cyan",
            )
        )
        self._login_loop()

        while True:
            self.console.print()
            self.console.print("[bold]主菜单[/bold]")
            self.console.print("1) 仪表盘")
            self.console.print("2) 订单 / 成交 / 持仓")
            self.console.print("3) 策略参数")
            self.console.print("4) 风控执行")
            self.console.print("5) API Key 管理")
            self.console.print("6) 系统配置")
            self.console.print("7) 告警中心")
            self.console.print("8) 导出 PnL CSV")
            self.console.print("9) 重新登录")
            self.console.print("0) 退出")

            choice = Prompt.ask("请选择操作", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], default="1")
            try:
                if choice == "1":
                    self.show_dashboard()
                elif choice == "2":
                    self.show_market_data()
                elif choice == "3":
                    self.manage_strategy()
                elif choice == "4":
                    self.manage_risk()
                elif choice == "5":
                    self.manage_api_keys()
                elif choice == "6":
                    self.manage_system_config()
                elif choice == "7":
                    self.manage_alerts()
                elif choice == "8":
                    self.export_pnl_csv()
                elif choice == "9":
                    self.api.clear_token()
                    self._login_loop()
                else:
                    self.console.print("[green]已退出 GLFT TUI。[/green]")
                    break
            except ApiError as exc:
                self.console.print(f"[red]请求失败：{exc}[/red]")

    def _login_loop(self) -> None:
        while True:
            self.console.print()
            self.console.print("[bold]请登录[/bold]")
            username = Prompt.ask("账号", default="admin").strip()
            password = getpass.getpass("密码: ")
            if not username or not password:
                self.console.print("[yellow]账号和密码不能为空。[/yellow]")
                continue
            try:
                self.api.login(username, password)
                profile = self.api.get_me()
                self.console.print(
                    f"[green]登录成功：{profile['username']}（{'启用' if profile['is_active'] else '禁用'}）[/green]"
                )
                return
            except ApiError as exc:
                self.console.print(f"[red]登录失败：{exc}[/red]")

    def show_dashboard(self) -> None:
        metrics = self.api.get_dashboard_metrics()
        table = Table(title="仪表盘指标", box=box.SIMPLE_HEAVY)
        table.add_column("指标", style="cyan")
        table.add_column("当前值", style="white")
        table.add_row("中间价", f"{metrics['mid_price']:.4f}")
        table.add_row("库存(BTC)", f"{metrics['inventory_btc']:.6f}")
        table.add_row("库存(USD)", f"{metrics['inventory_usd']:.2f}")
        table.add_row("未实现盈亏", f"{metrics['unrealized_pnl']:.2f}")
        table.add_row("挂单数量", str(metrics["open_orders"]))
        table.add_row("盘口价差", f"{metrics['spread']:.4f}")
        table.add_row("撤单率/分钟", f"{metrics['cancel_rate_per_min']:.2f}")
        table.add_row("下单率/分钟", f"{metrics['order_rate_per_min']:.2f}")
        self.console.print(table)
        self._pause()

    def show_market_data(self) -> None:
        orders = self.api.get_orders()
        trades = self.api.get_trades()
        positions = self.api.get_positions()
        self.console.print(self._build_table("订单（最近 50 条）", orders[:50], [
            ("order_id", "订单号"),
            ("symbol", "标的"),
            ("side", "方向"),
            ("price", "价格"),
            ("size", "数量"),
            ("status", "状态"),
        ]))
        self.console.print(self._build_table("成交（最近 50 条）", trades[:50], [
            ("trade_id", "成交号"),
            ("symbol", "标的"),
            ("side", "方向"),
            ("price", "价格"),
            ("size", "数量"),
            ("fee", "手续费"),
            ("realized_pnl", "已实现盈亏"),
        ]))
        self.console.print(self._build_table("持仓", positions, [
            ("symbol", "标的"),
            ("size", "仓位"),
            ("entry_price", "成本价"),
            ("mark_price", "标记价"),
            ("unrealized_pnl", "未实现盈亏"),
        ]))
        self._pause()

    def manage_strategy(self) -> None:
        params = self.api.get_strategy_params()
        self.console.print(self._build_kv_table("当前策略参数", params))
        if not Confirm.ask("是否更新策略参数？", default=False):
            return

        payload = {
            "gamma": self._prompt_float("gamma", params["gamma"]),
            "sigma": self._prompt_float("sigma", params["sigma"]),
            "A": self._prompt_float("A", params["A"]),
            "k": self._prompt_float("k", params["k"]),
            "time_horizon_seconds": self._prompt_int("time_horizon_seconds", params["time_horizon_seconds"]),
            "inventory_cap_usd": self._prompt_float("inventory_cap_usd", params["inventory_cap_usd"]),
            "order_cap_usd": self._prompt_float("order_cap_usd", params["order_cap_usd"]),
            "leverage_limit": self._prompt_float("leverage_limit", params["leverage_limit"]),
            "auto_tuning_enabled": Confirm.ask("启用自动调参？", default=bool(params["auto_tuning_enabled"])),
        }
        updated = self.api.update_strategy_params(payload)
        self.console.print("[green]策略参数更新成功。[/green]")
        self.console.print(self._build_kv_table("更新后策略参数", updated))
        self._pause()

    def manage_risk(self) -> None:
        status = self.api.get_risk_status()
        limits = self.api.get_risk_limits()
        self.console.print(self._build_kv_table("风控状态", status))
        self.console.print(self._build_kv_table("风控阈值", limits))

        while True:
            self.console.print("1) 启动引擎  2) 停止引擎  3) 更新风控阈值  0) 返回")
            choice = Prompt.ask("请选择", choices=["0", "1", "2", "3"], default="0")
            if choice == "0":
                return
            if choice == "1":
                self.api.engine_start()
                self.console.print("[green]引擎已启动。[/green]")
            elif choice == "2":
                self.api.engine_stop()
                self.console.print("[yellow]引擎已停止。[/yellow]")
            else:
                payload = {
                    "max_inventory_usd": self._prompt_float("max_inventory_usd", limits["max_inventory_usd"]),
                    "max_order_usd": self._prompt_float("max_order_usd", limits["max_order_usd"]),
                    "max_leverage": self._prompt_float("max_leverage", limits["max_leverage"]),
                    "max_cancel_rate_per_min": self._prompt_float(
                        "max_cancel_rate_per_min", limits["max_cancel_rate_per_min"]
                    ),
                    "max_order_rate_per_min": self._prompt_float(
                        "max_order_rate_per_min", limits["max_order_rate_per_min"]
                    ),
                }
                self.api.update_risk_limits(payload)
                self.console.print("[green]风控阈值已更新。[/green]")
            status = self.api.get_risk_status()
            limits = self.api.get_risk_limits()
            self.console.print(self._build_kv_table("风控状态", status))
            self.console.print(self._build_kv_table("风控阈值", limits))

    def manage_api_keys(self) -> None:
        current: dict[str, Any] | None = None
        try:
            current = self.api.get_keys()
            self.console.print(self._build_kv_table("已配置的 API Key 信息", current))
        except ApiError as exc:
            if exc.status_code == 404:
                self.console.print("[yellow]当前未配置 API Key。[/yellow]")
            else:
                raise

        if not Confirm.ask("是否更新 API Key？", default=True):
            return

        default_sub = current["sub_account_id"] if current else ""
        default_ip = current.get("ip_whitelist", "") if current else ""

        api_key = getpass.getpass("请输入 GRVT API Key: ").strip()
        private_key = getpass.getpass("请输入 GRVT Private Key: ").strip()
        if not api_key or not private_key:
            raise ApiError("API Key 与 Private Key 不能为空。")

        payload = {
            "api_key": api_key,
            "private_key": private_key,
            "sub_account_id": Prompt.ask("Sub Account ID", default=default_sub).strip(),
            "ip_whitelist": Prompt.ask("IP 白名单（逗号分隔）", default=default_ip).strip(),
        }
        if not payload["sub_account_id"]:
            raise ApiError("Sub Account ID 不能为空。")

        updated = self.api.save_keys(payload)
        self.console.print("[green]API Key 已更新。[/green]")
        self.console.print(self._build_kv_table("当前 API Key 信息", updated))
        self._pause()

    def manage_system_config(self) -> None:
        config = self.api.get_config()
        self.console.print(self._build_kv_table("系统配置", config))
        if not Confirm.ask("是否更新系统配置？", default=False):
            return

        payload = {
            "grvt_env": Prompt.ask("grvt_env", default=str(config["grvt_env"])).strip(),
            "grvt_symbol": Prompt.ask("grvt_symbol", default=str(config["grvt_symbol"])).strip(),
            "quote_interval_ms": self._prompt_int("quote_interval_ms", config["quote_interval_ms"]),
            "order_duration_secs": self._prompt_int("order_duration_secs", config["order_duration_secs"]),
            "calibration_window_days": self._prompt_int(
                "calibration_window_days", config["calibration_window_days"]
            ),
            "calibration_timeframe": Prompt.ask(
                "calibration_timeframe", default=str(config["calibration_timeframe"])
            ).strip(),
            "calibration_update_time": Prompt.ask(
                "calibration_update_time(HH:MM)", default=str(config["calibration_update_time"])
            ).strip(),
            "calibration_trade_sample": self._prompt_int(
                "calibration_trade_sample", config["calibration_trade_sample"]
            ),
            "log_retention_days": self._prompt_int("log_retention_days", config["log_retention_days"]),
            "alert_email_to": Prompt.ask("alert_email_to", default=str(config["alert_email_to"])).strip(),
            "smtp_host": Prompt.ask("smtp_host", default=str(config["smtp_host"])).strip(),
            "smtp_port": self._prompt_int("smtp_port", config["smtp_port"]),
            "smtp_user": Prompt.ask("smtp_user", default=str(config["smtp_user"])).strip(),
            "smtp_password": getpass.getpass("smtp_password（留空表示不更新）: ").strip(),
            "smtp_tls": Confirm.ask("启用 smtp_tls？", default=bool(config["smtp_tls"])),
        }
        updated = self.api.update_config(payload)
        self.console.print("[green]系统配置已更新。[/green]")
        self.console.print(self._build_kv_table("更新后系统配置", updated))
        self._pause()

    def manage_alerts(self) -> None:
        alerts = self.api.get_alerts()
        self.console.print(self._build_table("告警列表", alerts, [
            ("id", "ID"),
            ("level", "级别"),
            ("message", "内容"),
            ("is_read", "已读"),
        ]))
        unread_ids = [int(a["id"]) for a in alerts if not a.get("is_read", False)]
        if not unread_ids:
            self.console.print("[green]当前没有未读告警。[/green]")
            self._pause()
            return

        if not Confirm.ask("是否标记某条告警为已读？", default=False):
            return

        id_text = Prompt.ask("请输入告警 ID", default=str(unread_ids[0])).strip()
        alert_id = int(id_text)
        self.api.mark_alert_read(alert_id)
        self.console.print(f"[green]告警 {alert_id} 已标记为已读。[/green]")
        self._pause()

    def export_pnl_csv(self) -> None:
        content = self.api.export_pnl_csv()
        default_path = Path("reports") / f"pnl_{datetime.now():%Y%m%d_%H%M%S}.csv"
        save_path = Path(Prompt.ask("请输入导出路径", default=str(default_path)))
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(content, encoding="utf-8")
        self.console.print(f"[green]PnL 报表导出成功：{save_path}[/green]")
        self._pause()

    def _build_kv_table(self, title: str, data: dict[str, Any]) -> Table:
        table = Table(title=title, box=box.SIMPLE_HEAVY)
        table.add_column("字段", style="cyan")
        table.add_column("值", style="white")
        for key, value in data.items():
            table.add_row(str(key), str(value))
        return table

    def _build_table(
        self,
        title: str,
        rows: list[dict[str, Any]],
        columns: list[tuple[str, str]],
    ) -> Table:
        table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
        for _, label in columns:
            table.add_column(label, overflow="fold")
        if not rows:
            table.add_row(*(["-"] * len(columns)))
            return table
        for row in rows:
            table.add_row(*(str(row.get(field, "")) for field, _ in columns))
        return table

    def _prompt_float(self, name: str, default: float) -> float:
        while True:
            value = Prompt.ask(name, default=str(default)).strip()
            try:
                return float(value)
            except ValueError:
                self.console.print(f"[red]{name} 必须是数字。[/red]")

    def _prompt_int(self, name: str, default: int) -> int:
        while True:
            value = Prompt.ask(name, default=str(default)).strip()
            try:
                return int(value)
            except ValueError:
                self.console.print(f"[red]{name} 必须是整数。[/red]")

    def _pause(self) -> None:
        Prompt.ask("按回车继续", default="")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GLFT 终端控制台（TUI）")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000/api",
        help="后端 API 地址（默认: http://127.0.0.1:8000/api）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    console = Console()
    api = GlftApiClient(base_url=args.api_url)
    app = GlftTuiApp(api=api, console=console)
    try:
        app.run()
    finally:
        api.close()


if __name__ == "__main__":
    main()
