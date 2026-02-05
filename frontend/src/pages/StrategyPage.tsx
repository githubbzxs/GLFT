import { useEffect, useState } from "react";
import api from "../api/client";

type Params = {
  gamma: number;
  sigma: number;
  A: number;
  k: number;
  time_horizon_seconds: number;
  inventory_cap_usd: number;
  order_cap_usd: number;
  leverage_limit: number;
  auto_tuning_enabled: boolean;
};

export default function StrategyPage() {
  const [params, setParams] = useState<Params | null>(null);
  const [message, setMessage] = useState("");

  const load = async () => {
    const res = await api.get("/strategy/params");
    setParams(res.data);
  };

  useEffect(() => {
    load();
  }, []);

  const update = async () => {
    if (!params) return;
    await api.post("/strategy/params", params);
    setMessage("已更新策略参数");
    setTimeout(() => setMessage(""), 2000);
  };

  if (!params) return null;

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">策略参数</div>
        <button className="btn" onClick={update}>
          保存参数
        </button>
      </div>
      {message && <div className="panel">{message}</div>}
      <div className="panel form-grid">
        <label>
          风险厌恶 gamma
          <input
            type="number"
            value={params.gamma}
            onChange={(e) => setParams({ ...params, gamma: Number(e.target.value) })}
          />
        </label>
        <label>
          波动率 sigma
          <input
            type="number"
            value={params.sigma}
            onChange={(e) => setParams({ ...params, sigma: Number(e.target.value) })}
          />
        </label>
        <label>
          到达强度 A
          <input
            type="number"
            value={params.A}
            onChange={(e) => setParams({ ...params, A: Number(e.target.value) })}
          />
        </label>
        <label>
          斜率 k
          <input
            type="number"
            value={params.k}
            onChange={(e) => setParams({ ...params, k: Number(e.target.value) })}
          />
        </label>
        <label>
          时间视窗(秒)
          <input
            type="number"
            value={params.time_horizon_seconds}
            onChange={(e) =>
              setParams({ ...params, time_horizon_seconds: Number(e.target.value) })
            }
          />
        </label>
        <label>
          库存上限(USD)
          <input
            type="number"
            value={params.inventory_cap_usd}
            onChange={(e) =>
              setParams({ ...params, inventory_cap_usd: Number(e.target.value) })
            }
          />
        </label>
        <label>
          单笔上限(USD)
          <input
            type="number"
            value={params.order_cap_usd}
            onChange={(e) => setParams({ ...params, order_cap_usd: Number(e.target.value) })}
          />
        </label>
        <label>
          杠杆上限
          <input
            type="number"
            value={params.leverage_limit}
            onChange={(e) => setParams({ ...params, leverage_limit: Number(e.target.value) })}
          />
        </label>
        <label>
          自动调参
          <select
            value={params.auto_tuning_enabled ? "true" : "false"}
            onChange={(e) =>
              setParams({ ...params, auto_tuning_enabled: e.target.value === "true" })
            }
          >
            <option value="true">开启</option>
            <option value="false">关闭</option>
          </select>
        </label>
      </div>
    </div>
  );
}
