import { useEffect, useState } from "react";
import api from "../api/client";

export default function ApiKeysPage() {
  const [apiKey, setApiKey] = useState("");
  const [privateKey, setPrivateKey] = useState("");
  const [subAccountId, setSubAccountId] = useState("");
  const [ipWhitelist, setIpWhitelist] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    try {
      const res = await api.get("/keys");
      setSubAccountId(res.data.sub_account_id);
      setIpWhitelist(res.data.ip_whitelist || "");
    } catch {
      // 未配置时忽略
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    await api.post("/keys", {
      api_key: apiKey,
      private_key: privateKey,
      sub_account_id: subAccountId,
      ip_whitelist: ipWhitelist
    });
    setMessage("密钥已保存（服务端加密）");
    setApiKey("");
    setPrivateKey("");
    setTimeout(() => setMessage(""), 2000);
  };

  return (
    <div>
      <div className="top-bar">
        <div className="top-title">API Key 管理</div>
        <button className="btn" onClick={save}>
          保存密钥
        </button>
      </div>
      {message && <div className="panel">{message}</div>}
      <div className="panel form-grid">
        <label>
          GRVT API Key
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
        </label>
        <label>
          GRVT Private Key
          <input value={privateKey} onChange={(e) => setPrivateKey(e.target.value)} />
        </label>
        <label>
          Sub Account ID
          <input value={subAccountId} onChange={(e) => setSubAccountId(e.target.value)} />
        </label>
        <label>
          IP 白名单
          <input value={ipWhitelist} onChange={(e) => setIpWhitelist(e.target.value)} />
        </label>
      </div>
      <div className="panel">
        <p style={{ margin: 0, color: "#64748b" }}>
          密钥只在输入时出现，保存后不会回显。
        </p>
      </div>
    </div>
  );
}
