import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { Spinner } from '../components/Spinner';
import { StatCard } from '../components/StatCard';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function formatDate(value) {
  return new Date(value).toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function ProjectPage() {
  const { projectId } = useParams();
  const nav = useNavigate();
  const { activeProject, activeProjectError, fetchProject, deleteProject } = useStore();
  const [loading, setLoading] = useState(true);
  const project = activeProject?.id === projectId ? activeProject : null;

  useDocumentTitle(project?.name || 'Progetto');

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      try {
        await fetchProject(projectId);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [fetchProject, projectId]);

  if (loading) {
    return (
      <div className="content content--centered">
        <div className="empty-state">
          <Spinner size={48} centered label="Caricamento progetto..." />
        </div>
      </div>
    );
  }

  if (activeProjectError && !project) {
    return (
      <div className="content page-shell">
        <div className="alert alert--error" role="alert">
          <span>Connessione progetto non riuscita.</span>
          <span>{activeProjectError}</span>
        </div>
        <div className="u-mt-4">
          <Link to="/" className="btn btn--secondary">Torna ai progetti</Link>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="content page-shell">
        <div className="empty-state">
          <div className="empty-state__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4" />
              <path d="M12 16h.01" />
            </svg>
          </div>
          <h3 className="empty-state__title">Progetto non trovato</h3>
          <p className="empty-state__description">
            Il progetto richiesto non esiste oppure non e disponibile nel workspace corrente.
          </p>
          <Link to="/" className="btn btn--secondary u-mt-4">Torna ai progetti</Link>
        </div>
      </div>
    );
  }

  const datasets = project.datasets || [];
  const datasetCount = datasets.length;
  const totalRows = datasets.reduce((sum, dataset) => sum + (dataset.n_rows || 0), 0);
  const widestDataset = datasets.reduce((max, dataset) => Math.max(max, dataset.n_cols || 0), 0);
  const lastUpload = datasets
    .map(dataset => dataset.created_at)
    .sort((left, right) => new Date(right) - new Date(left))[0];

  return (
    <div className="content page-shell">
      <section className="hero">
        <div className="hero__main">
          <nav className="topbar__breadcrumb" aria-label="Breadcrumb">
            <Link to="/">Progetti</Link>
            <span className="topbar__breadcrumb-separator">/</span>
            <span aria-current="page">{project.name}</span>
          </nav>
          <span className="hero__eyebrow">Workspace Control</span>
          <h1 className="hero__title">{project.name}</h1>
          <p className="hero__lede">
            {project.description || 'Workspace dedicato alla gestione di dataset, run e output enterprise.'}
          </p>
          <div className="hero__actions">
            <Link to={`/projects/${projectId}/upload`} className="btn btn--primary btn--lg">
              Carica dataset
            </Link>
            <button
              className="btn btn--secondary btn--lg"
              onClick={async () => {
                if (window.confirm('Vuoi davvero eliminare questo progetto e tutti i file associati?')) {
                  await deleteProject(projectId);
                  nav('/');
                }
              }}
            >
              Elimina progetto
            </button>
          </div>
        </div>

        <div className="hero__rail">
          <div className="hero-stat">
            <span className="hero-stat__label">Dataset registrati</span>
            <strong className="hero-stat__value">{datasetCount}</strong>
            <span className="hero-stat__meta">inventory del workspace</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Righe aggregate</span>
            <strong className="hero-stat__value">{totalRows.toLocaleString('it-IT')}</strong>
            <span className="hero-stat__meta">somma dei dataset caricati</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Ultimo upload</span>
            <strong className="hero-stat__value">{lastUpload ? formatDate(lastUpload) : 'N/A'}</strong>
            <span className="hero-stat__meta">colonne max {widestDataset || 0}</span>
          </div>
        </div>
      </section>

      {activeProjectError && (
        <div className="alert alert--error" role="alert">
          <span>Aggiornamento progetto non riuscito.</span>
          <span>{activeProjectError}</span>
        </div>
      )}

      <div className="metrics-strip">
        <StatCard label="Dataset" value={datasetCount} accent={datasetCount > 0} />
        <StatCard label="Righe totali" value={totalRows} />
        <StatCard label="Ampiezza massima" value={widestDataset || 'N/A'} />
      </div>

      <div className="workspace-grid">
        <section className="card card--accent">
          <div className="card__header">
            <div className="card__header-left">
              <span className="card__eyebrow">Dataset Inventory</span>
              <h2 className="card__title">Dataset caricati</h2>
              <p className="card__subtitle">
                Il workspace centralizza gli asset caricati e apre nuove run dal canvas di upload.
              </p>
            </div>
          </div>

          {datasetCount === 0 ? (
            <div className="empty-state empty-state--compact">
              <div className="empty-state__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 16V4" />
                  <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
                  <path d="M4 19.5h16" />
                </svg>
              </div>
              <h3 className="empty-state__title">Nessun dataset disponibile</h3>
              <p className="empty-state__description">
                Carica il primo file per passare alla configurazione dell'analisi.
              </p>
            </div>
          ) : (
            <div className="table-container">
              <table className="table" aria-label="Dataset caricati">
                <thead>
                  <tr>
                    <th>Nome file</th>
                    <th className="numeric">Righe</th>
                    <th className="numeric">Colonne</th>
                    <th>Caricato il</th>
                    <th>Azione</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map(dataset => (
                    <tr key={dataset.id}>
                      <td className="u-font-medium">{dataset.filename}</td>
                      <td className="numeric">{dataset.n_rows.toLocaleString('it-IT')}</td>
                      <td className="numeric">{dataset.n_cols}</td>
                      <td>{formatDate(dataset.created_at)}</td>
                      <td>
                        <Link to={`/projects/${projectId}/upload`} className="btn btn--secondary btn--sm">
                          Nuova analisi
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="rail-stack">
          <div className="card">
            <div className="card__header">
              <div className="card__header-left">
                <span className="card__eyebrow">Run Flow</span>
                <h2 className="card__title">Cosa succede dopo</h2>
              </div>
            </div>
            <div className="stack-list">
              <div className="stack-list__item">
                <span className="stack-list__index">01</span>
                <p>Carichi il dataset e validi schema, target e feature candidate.</p>
              </div>
              <div className="stack-list__item">
                <span className="stack-list__index">02</span>
                <p>Lanci l'analisi e apri il canvas con sezioni executive, EDA e governance.</p>
              </div>
              <div className="stack-list__item">
                <span className="stack-list__index">03</span>
                <p>Produci report PDF e deliverable senza uscire dal workspace.</p>
              </div>
            </div>
          </div>

          <div className="card card--muted">
            <div className="card__header">
              <div className="card__header-left">
                <span className="card__eyebrow">Status Snapshot</span>
                <h2 className="card__title">Readiness del progetto</h2>
              </div>
            </div>
            <div className="meta-list">
              <div className="meta-list__row">
                <span>Workspace</span>
                <strong>{project.name}</strong>
              </div>
              <div className="meta-list__row">
                <span>Dataset presenti</span>
                <strong>{datasetCount}</strong>
              </div>
              <div className="meta-list__row">
                <span>Pronto a nuova run</span>
                <strong>{datasetCount > 0 ? 'Si' : 'In attesa'}</strong>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default ProjectPage;
