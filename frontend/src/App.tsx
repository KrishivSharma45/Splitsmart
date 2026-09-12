import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import { AuditLedgerPage } from "./pages/AuditLedgerPage";
import { Dashboard } from "./pages/Dashboard";
import { ExpenseDetail } from "./pages/ExpenseDetail";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { ReportsPage } from "./pages/ReportsPage";
import { SecurityCenter } from "./pages/SecurityCenter";
import { Settings } from "./pages/Settings";
import { TripDetail } from "./pages/TripDetail";
import { Trips } from "./pages/Trips";

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <Routes>
      <Route path="/" element={isLoading ? null : isAuthenticated ? <Navigate to="/dashboard" replace /> : <Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trips" element={<Trips />} />
        <Route path="/trips/:tripId" element={<TripDetail />} />
        <Route path="/trips/:tripId/expenses/:expenseId" element={<ExpenseDetail />} />
        <Route path="/trips/:tripId/reports" element={<ReportsPage />} />
        <Route path="/security" element={<SecurityCenter />} />
        <Route path="/audit" element={<AuditLedgerPage />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
