import { useEffect, useState } from "react";
import api from "../api/client";

type Order = {
  order_id: string;
  symbol: string;
  side: string;
  price: number;
  size: number;
  status: string;
};

type Trade = {
  trade_id: string;
  symbol: string;
  side: string;
  price: number;
  size: number;
  fee: number;
  realized_pnl: number;
};

type Position = {
  symbol: string;
  size: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
};

export default function OrdersPage() {
  const [tab, setTab] = useState<"orders" | "trades" | "positions">("orders");
  const [orders, setOrders] = useState<Order[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);

  const load = async () => {
    const [o, t, p] = await Promise.all([
      api.get("/orders"),
      api.get("/trades"),
      api.get("/positions")
    ]);
    setOrders(o.data);
    setTrades(t.data);
    setPositions(p.data);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">订单 / 成交 / 持仓</div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn outline" onClick={() => setTab("orders")}>
            订单
          </button>
          <button className="btn outline" onClick={() => setTab("trades")}>
            成交
          </button>
          <button className="btn outline" onClick={() => setTab("positions")}>
            持仓
          </button>
        </div>
      </div>

      {tab === "orders" && (
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>订单号</th>
                <th>方向</th>
                <th>价格</th>
                <th>数量</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.order_id}>
                  <td>{o.order_id}</td>
                  <td>{o.side}</td>
                  <td>{o.price.toFixed(2)}</td>
                  <td>{o.size}</td>
                  <td>
                    <span className="badge">{o.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "trades" && (
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>成交号</th>
                <th>方向</th>
                <th>价格</th>
                <th>数量</th>
                <th>手续费</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.trade_id}>
                  <td>{t.trade_id}</td>
                  <td>{t.side}</td>
                  <td>{t.price.toFixed(2)}</td>
                  <td>{t.size}</td>
                  <td>{t.fee}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "positions" && (
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>标的</th>
                <th>持仓</th>
                <th>成本价</th>
                <th>标记价</th>
                <th>未实现盈亏</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.symbol}>
                  <td>{p.symbol}</td>
                  <td>{p.size}</td>
                  <td>{p.entry_price.toFixed(2)}</td>
                  <td>{p.mark_price.toFixed(2)}</td>
                  <td>{p.unrealized_pnl.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
