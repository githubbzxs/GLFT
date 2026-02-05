import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await api.post("/auth/login", { username, password });
      localStorage.setItem("token", res.data.access_token);
      navigate("/");
    } catch {
      setError("登录失败，请检查账号和密码");
    }
  };

  return (
    <div className="login-wrapper">
      <section className="login-hero">
        <h1 style={{ margin: 0, fontFamily: "Space Grotesk, sans-serif" }}>
          GLFT 做市系统
        </h1>
        <p>以 GLFT 模型驱动的主网 BTC 永续做市引擎，集成风控、告警与参数调优。</p>
        <div className="card" style={{ background: "rgba(255,255,255,0.08)", color: "#e2e8f0" }}>
          <p style={{ margin: 0 }}>建议先在小仓位下验证策略稳定性。</p>
        </div>
      </section>
      <section className="login-box">
        <form className="login-card" onSubmit={handleLogin}>
          <h2>登录</h2>
          <label>
            账号
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            密码
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error && <p style={{ color: "#dc2626" }}>{error}</p>}
          <button className="btn" type="submit">
            进入系统
          </button>
        </form>
      </section>
    </div>
  );
}
