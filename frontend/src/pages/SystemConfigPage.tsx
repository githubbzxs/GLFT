import { useEffect, useState } from "react";
import api from "../api/client";

type Config = {
  grvt_env: string;
  grvt_symbol: string;
  quote_interval_ms: number;
  order_duration_secs: number;
  calibration_window_days: number;
  calibration_timeframe: string;
  calibration_update_time: string;
  calibration_trade_sample: number;
  log_retention_days: number;
  alert_email_to: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password_set: boolean;
  smtp_tls: boolean;
};

export default function SystemConfigPage() {
  const [config, setConfig] = useState<Config | null>(null);
  const [smtpPassword, setSmtpPassword] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const res = await api.get("/config");
    setConfig(res.data);
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    if (!config) return;
    await api.post("/config", {
      ...config,
      smtp_password: smtpPassword
    });
    setMessage("配置已保存，部分变更需要重启引擎生效");
    setTimeout(() => setMessage(""), 2000);
    setSmtpPassword("");
    load();
  };

  if (!config) return null;

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">系统配置</div>
        <button className="btn" onClick={save}>
          保存配置
        </button>
      </div>
      {message && <div className="panel">{message}</div>}
      <div className="panel form-grid">
        <label>
          GRVT 环境
          <select
            value={config.grvt_env}
            onChange={(e) => setConfig({ ...config, grvt_env: e.target.value })}
          >
            <option value="prod">prod</option>
            <option value="testnet">testnet</option>
            <option value="staging">staging</option>
            <option value="dev">dev</option>
          </select>
        </label>
        <label>
          交易标的
          <input
            value={config.grvt_symbol}
            onChange={(e) => setConfig({ ...config, grvt_symbol: e.target.value })}
          />
        </label>
        <label>
          报价间隔(ms)
          <input
            type="number"
            value={config.quote_interval_ms}
            onChange={(e) => setConfig({ ...config, quote_interval_ms: Number(e.target.value) })}
          />
        </label>
        <label>
          订单有效期(秒)
          <input
            type="number"
            value={config.order_duration_secs}
            onChange={(e) =>
              setConfig({ ...config, order_duration_secs: Number(e.target.value) })
            }
          />
        </label>
        <label>
          回推窗口(天)
          <input
            type="number"
            value={config.calibration_window_days}
            onChange={(e) =>
              setConfig({ ...config, calibration_window_days: Number(e.target.value) })
            }
          />
        </label>
        <label>
          回推周期
          <input
            value={config.calibration_timeframe}
            onChange={(e) =>
              setConfig({ ...config, calibration_timeframe: e.target.value })
            }
          />
        </label>
        <label>
          回推执行时间(HH:MM)
          <input
            value={config.calibration_update_time}
            onChange={(e) =>
              setConfig({ ...config, calibration_update_time: e.target.value })
            }
          />
        </label>
        <label>
          回推样本数
          <input
            type="number"
            value={config.calibration_trade_sample}
            onChange={(e) =>
              setConfig({ ...config, calibration_trade_sample: Number(e.target.value) })
            }
          />
        </label>
        <label>
          日志留存(天)
          <input
            type="number"
            value={config.log_retention_days}
            onChange={(e) =>
              setConfig({ ...config, log_retention_days: Number(e.target.value) })
            }
          />
        </label>
      </div>
      <div className="panel form-grid">
        <label>
          告警邮箱
          <input
            value={config.alert_email_to}
            onChange={(e) => setConfig({ ...config, alert_email_to: e.target.value })}
          />
        </label>
        <label>
          SMTP Host
          <input
            value={config.smtp_host}
            onChange={(e) => setConfig({ ...config, smtp_host: e.target.value })}
          />
        </label>
        <label>
          SMTP 端口
          <input
            type="number"
            value={config.smtp_port}
            onChange={(e) => setConfig({ ...config, smtp_port: Number(e.target.value) })}
          />
        </label>
        <label>
          SMTP 用户
          <input
            value={config.smtp_user}
            onChange={(e) => setConfig({ ...config, smtp_user: e.target.value })}
          />
        </label>
        <label>
          SMTP 密码 {config.smtp_password_set ? "(已设置)" : ""}
          <input
            value={smtpPassword}
            placeholder="留空则不更新"
            onChange={(e) => setSmtpPassword(e.target.value)}
          />
        </label>
        <label>
          SMTP TLS
          <select
            value={config.smtp_tls ? "true" : "false"}
            onChange={(e) => setConfig({ ...config, smtp_tls: e.target.value === "true" })}
          >
            <option value="true">开启</option>
            <option value="false">关闭</option>
          </select>
        </label>
      </div>
      <div className="panel">
        <p style={{ margin: 0, color: "#64748b" }}>
          GRVT API Key 与私钥请在“API Key 管理”页面配置。修改环境或交易标的会触发引擎重建。
        </p>
      </div>
    </div>
  );
}
