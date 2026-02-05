import { useEffect, useState } from "react";
import api from "../api/client";

type RiskStatus = {
  is_trading: boolean;
  last_event?: string;
  cancel_rate_per_min: number;
  order_rate_per_min: number;
};

type Limits = {
  max_inventory_usd: number;
  max_order_usd: number;
  max_leverage: number;
  max_cancel_rate_per_min: number;
  max_order_rate_per_min: number;
};

export default function RiskPage() {
  const [status, setStatus] = useState<RiskStatus | null>(null);
  const [limits, setLimits] = useState<Limits>({
    max_inventory_usd: 100,
    max_order_usd: 20,
    max_leverage: 50,
    max_cancel_rate_per_min: 0.85,
    max_order_rate_per_min: 120
  });

  const load = async () => {
    const res = await api.get("/risk/status");
    setStatus(res.data);
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, []);

  const update = async () => {
    await api.post("/risk/limits", limits);
  };

  const start = async () => {
    await api.post("/engine/start");
    load();
  };

  const stop = async () => {
    await api.post("/engine/stop");
    load();
  };

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">风控与执行</div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={start}>
            启动引擎
          </button>
          <button className="btn secondary" onClick={stop}>
            停止引擎
          </button>
        </div>
      </div>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>状态</h3>
        <p>引擎状态：{status?.is_trading ? "运行中" : "已停止"}</p>
        <p>最近事件：{status?.last_event || "无"}</p>
        <p>撤单率/分钟：{status?.cancel_rate_per_min?.toFixed(2) || "-"}</p>
        <p>下单率/分钟：{status?.order_rate_per_min?.toFixed(2) || "-"}</p>
      </div>
      <div className="panel form-grid">
        <label>
          最大库存(USD)
          <input
            type="number"
            value={limits.max_inventory_usd}
            onChange={(e) =>
              setLimits({ ...limits, max_inventory_usd: Number(e.target.value) })
            }
          />
        </label>
        <label>
          单笔上限(USD)
          <input
            type="number"
            value={limits.max_order_usd}
            onChange={(e) => setLimits({ ...limits, max_order_usd: Number(e.target.value) })}
          />
        </label>
        <label>
          最大杠杆
          <input
            type="number"
            value={limits.max_leverage}
            onChange={(e) => setLimits({ ...limits, max_leverage: Number(e.target.value) })}
          />
        </label>
        <label>
          最大撤单率/分钟
          <input
            type="number"
            value={limits.max_cancel_rate_per_min}
            onChange={(e) =>
              setLimits({ ...limits, max_cancel_rate_per_min: Number(e.target.value) })
            }
          />
        </label>
        <label>
          最大下单率/分钟
          <input
            type="number"
            value={limits.max_order_rate_per_min}
            onChange={(e) =>
              setLimits({ ...limits, max_order_rate_per_min: Number(e.target.value) })
            }
          />
        </label>
      </div>
      <button className="btn" onClick={update}>
        更新风控阈值
      </button>
    </div>
  );
}
