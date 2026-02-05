import type { JSX } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { clearToken, getToken, isTokenExpired } from "./api/session";
import Layout from "./components/Layout";
import AlertsPage from "./pages/AlertsPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import OrdersPage from "./pages/OrdersPage";
import RiskPage from "./pages/RiskPage";
import StrategyPage from "./pages/StrategyPage";
import SystemConfigPage from "./pages/SystemConfigPage";

type LoginState = {
  reason?: "missing" | "expired" | "unauthorized";
  from?: string;
};

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const location = useLocation();
  const token = getToken();

  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ reason: "missing", from: location.pathname } satisfies LoginState}
      />
    );
  }

  if (isTokenExpired(token)) {
    clearToken();
    return (
      <Navigate
        to="/login"
        replace
        state={{ reason: "expired", from: location.pathname } satisfies LoginState}
      />
    );
  }

  return children;
};

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="strategy" element={<StrategyPage />} />
        <Route path="risk" element={<RiskPage />} />
        <Route path="keys" element={<ApiKeysPage />} />
        <Route path="config" element={<SystemConfigPage />} />
        <Route path="alerts" element={<AlertsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
