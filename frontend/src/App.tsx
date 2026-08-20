import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { OverviewPage } from "@/pages/OverviewPage";
import { CasesPage } from "@/pages/CasesPage";
import { CaseDetailPage } from "@/pages/CaseDetailPage";
import { ShowcasePage } from "@/pages/ShowcasePage";
import { CaseComparisonPage } from "@/pages/CaseComparisonPage";
import { EvaluationsPage } from "@/pages/EvaluationsPage";
import { ArchitecturePage } from "@/pages/ArchitecturePage";
import { ObservabilityPage } from "@/pages/ObservabilityPage";
import { AboutPage } from "@/pages/AboutPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<OverviewPage />} />
          <Route path="cases" element={<CasesPage />} />
          <Route path="cases/:caseId" element={<CaseDetailPage />} />
          <Route path="showcase" element={<ShowcasePage />} />
          <Route path="showcase/:evalId" element={<CaseComparisonPage />} />
          <Route path="evaluations" element={<EvaluationsPage />} />
          <Route path="architecture" element={<ArchitecturePage />} />
          <Route path="observability" element={<ObservabilityPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
