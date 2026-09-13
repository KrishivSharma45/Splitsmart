import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PageSpinner } from "./components/ui/Spinner";
import { useAuth } from "./context/AuthContext";

// Route-level code splitting: each page (and whatever it pulls in, e.g.
// recharts for Dashboard/ReportsPage) ships as its own chunk, fetched only
// when that route is actually visited, instead of one large bundle.
const Landing = lazy(() => import("./pages/Landing").then((m) => ({ default: m.Landing })));
const Login = lazy(() => import("./pages/Login").then((m) => ({ default: m.Login })));
const Register = lazy(() => import("./pages/Register").then((m) => ({ default: m.Register })));
const Dashboard = lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const Trips = lazy(() => import("./pages/Trips").then((m) => ({ default: m.Trips })));
const TripDetail = lazy(() => import("./pages/TripDetail").then((m) => ({ default: m.TripDetail })));
const ExpenseDetail = lazy(() => import("./pages/ExpenseDetail").then((m) => ({ default: m.ExpenseDetail })));
const ReportsPage = lazy(() => import("./pages/ReportsPage").then((m) => ({ default: m.ReportsPage })));
const SecurityCenter = lazy(() => import("./pages/SecurityCenter").then((m) => ({ default: m.SecurityCenter })));
const AuditLedgerPage = lazy(() => import("./pages/AuditLedgerPage").then((m) => ({ default: m.AuditLedgerPage })));
const Settings = lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings })));

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <Suspense fallback={<PageSpinner />}>
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
    </Suspense>
  );
}
