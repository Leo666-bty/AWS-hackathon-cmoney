import { Navigate, Route, Routes } from "react-router-dom";
import { FoundationRoute } from "../routes/FoundationRoute";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<FoundationRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
