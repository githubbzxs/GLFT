import { useEffect, useState } from "react";
import api from "../api/client";

type Metrics = {
  mid_price: number;
  inventory_btc: number;
  inventory_usd: number;
  unrealized_pnl: number;
  open_orders: number;
  spread: number;
  cancel_rate_per_min: number;
  order_rate_per_min: number;
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  const load = async () => {
    const res = await api.get("/dashboard/metrics");
    setMetrics(res.data);
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">仪表盘</div>
      </div>
      <div className="card-grid">
        <div className="card">
          <h4>中间价</h4>
          <div className="value">{metrics?.mid_price?.toFixed(2) || "-"}</div>
        </div>
        <div className="card">
          <h4>库存(BTC)</h4>
          <div className="value">{metrics?.inventory_btc?.toFixed(4) || "-"}</div>
        </div>
        <div className="card">
          <h4>库存(USD)</h4>
          <div className="value">{metrics?.inventory_usd?.toFixed(2) || "-"}</div>
        </div>
        <div className="card">
          <h4>未实现盈亏</h4>
          <div className="value">{metrics?.unrealized_pnl?.toFixed(2) || "-"}</div>
        </div>
        <div className="card">
          <h4>挂单数量</h4>
          <div className="value">{metrics?.open_orders ?? "-"}</div>
        </div>
        <div className="card">
          <h4>盘口价差</h4>
          <div className="value">{metrics?.spread?.toFixed(2) || "-"}</div>
        </div>
      </div>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>风控速览</h3>
        <div className="card-grid">
          <div className="card">
            <h4>撤单率/分钟</h4>
            <div className="value">{metrics?.cancel_rate_per_min?.toFixed(1) || "-"}</div>
          </div>
          <div className="card">
            <h4>下单率/分钟</h4>
            <div className="value">{metrics?.order_rate_per_min?.toFixed(1) || "-"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
