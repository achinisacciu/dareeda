import { Suspense, lazy, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { SpinnerAccent } from './components/Spinner';
import { useStore } from './store/useStore';

const HomePage = lazy(() => import('./pages/HomePage'));
const ProjectPage = lazy(() => import('./pages/ProjectPage'));
const UploadPage = lazy(() => import('./pages/UploadPage'));
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'));

function RouteFallback() {
  return (
    <div className="content content--centered">
      <div className="empty-state" role="status" aria-label="Caricamento pagina">
        <SpinnerAccent size={42} />
        <p className="u-mt-4 u-text-secondary">Caricamento pagina...</p>
      </div>
    </div>
  );
}

function resolveShellMeta(pathname) {
  if (pathname.startsWith('/analysis/')) {
    return {
      eyebrow: 'Executive Intelligence',
      title: 'Analysis Workspace',
      summary: 'Leggi gli output tecnici, executive e di governance in un unico canvas.',
    };
  }

  if (pathname.includes('/upload')) {
    return {
      eyebrow: 'Analysis Configuration',
      title: 'Dataset Intake',
      summary: 'Carica, valida e orchestra la configurazione prima di lanciare l\'EDA.',
    };
  }

  if (pathname.startsWith('/projects/')) {
    return {
      eyebrow: 'Workspace Control',
      title: 'Project Operations',
      summary: 'Gestisci dataset, run attive e readiness operativa del workspace.',
    };
  }

  return {
    eyebrow: 'Data Intelligence Workspace',
    title: 'Project Registry',
    summary: 'Costruisci workspace analitici con output completi, tracciabili e pronti alla consegna.',
  };
}

function Topbar() {
  const location = useLocation();
  const projects = useStore(state => state.projects);
  const activeProject = useStore(state => state.activeProject);

  const meta = useMemo(() => resolveShellMeta(location.pathname), [location.pathname]);
  const uploadProjectId = activeProject?.id || projects[0]?.id || null;
  const launchHref = uploadProjectId ? `/projects/${uploadProjectId}/upload` : '/';

  return (
    <header className="topbar">
      <div className="topbar__left">
        <div className="topbar__brandblock">
          <span className="topbar__eyebrow">{meta.eyebrow}</span>
          <div className="topbar__copy">
            <div className="topbar__title">{meta.title}</div>
            <p className="topbar__summary">{meta.summary}</p>
          </div>
        </div>

        <nav className="topbar__nav" aria-label="Global">
          <Link to="/" className="topbar__nav-link">Projects</Link>
          {activeProject?.id && (
            <Link to={`/projects/${activeProject.id}`} className="topbar__nav-link">
              Active Workspace
            </Link>
          )}
        </nav>
      </div>

      <div className="topbar__right">
        <label className="topbar__search" aria-label="Workspace search">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <input
            className="topbar__search-input"
            placeholder="Search projects, datasets, outputs"
            type="text"
          />
        </label>

        <div className="topbar__status-pill">
          <span className="topbar__status-value">{projects.length}</span>
          <span className="topbar__status-label">workspace</span>
        </div>

        <Link className="btn btn--primary topbar__cta" to={launchHref}>
          {uploadProjectId ? 'New Analysis' : 'Create Workspace'}
        </Link>
      </div>
    </header>
  );
}

function ShellLayout() {
  return (
    <div className="dashboard">
      <Sidebar />
      <div className="shell-frame">
        <Topbar />
        <main className="main">
          <Suspense fallback={<RouteFallback />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/projects/:projectId" element={<ProjectPage />} />
              <Route path="/projects/:projectId/upload" element={<UploadPage />} />
              <Route path="/analysis/:analysisId" element={<AnalysisPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <ShellLayout />
    </BrowserRouter>
  );
}
