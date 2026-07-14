import { Navigate, Route, Routes } from "react-router-dom";
import { ReconstructionProvider } from "../features/reconstruction/ReconstructionContext";
import { BuilderRoute } from "../routes/BuilderRoute";
import { LandingRoute } from "../routes/LandingRoute";
import { ReconstructionRoute } from "../routes/ReconstructionRoute";
import { ResultRoute } from "../routes/ResultRoute";
import { AppHeader } from "../shared/components/AppHeader";

export function App() {
  return (
    <ReconstructionProvider>
      <AppHeader />
      <Routes>
        <Route path="/" element={<LandingRoute />} />
        <Route path="/builder" element={<BuilderRoute />} />
        <Route path="/reconstruct/:index" element={<ReconstructionRoute />} />
        <Route path="/result" element={<ResultRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ReconstructionProvider>
  );
}
