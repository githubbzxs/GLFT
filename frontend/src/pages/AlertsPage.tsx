import { useEffect, useState } from "react";
import api from "../api/client";

type Alert = {
  id: number;
  level: string;
  message: string;
  is_read: boolean;
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const load = async () => {
    const res = await api.get("/alerts");
    setAlerts(res.data);
  };

  useEffect(() => {
    load();
  }, []);

  const markRead = async (id: number) => {
    await api.post(`/alerts/${id}/read`);
    load();
  };

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">告警</div>
      </div>
      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>级别</th>
              <th>内容</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td>{a.level}</td>
                <td>{a.message}</td>
                <td>
                  <span className={`badge ${a.is_read ? "" : "warn"}`}>
                    {a.is_read ? "已读" : "未读"}
                  </span>
                </td>
                <td>
                  {!a.is_read && (
                    <button className="btn outline" onClick={() => markRead(a.id)}>
                      标记已读
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
