import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import OrdersPage from "./pages/OrdersPage";
import StrategyPage from "./pages/StrategyPage";
import RiskPage from "./pages/RiskPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import AlertsPage from "./pages/AlertsPage";
import SystemConfigPage from "./pages/SystemConfigPage";

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const token = localStorage.getItem("token");
  if (!token) {
    return <Navigate to="/login" replace />;
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
    </Routes>
  );
}
