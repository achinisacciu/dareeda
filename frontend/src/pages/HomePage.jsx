import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { Spinner } from '../components/Spinner';
import { StatCard } from '../components/StatCard';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

function formatProjectDate(value) {
  return new Date(value).toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function HomePage() {
  const { projects, loadingProjects, projectsError, fetchProjects, createProject } = useStore();
  const nav = useNavigate();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [error, setError] = useState(null);

  useDocumentTitle('Progetti');

  useEffect(() => { fetchProjects(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!name.trim()) {
      setError('Inserisci un nome progetto');
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const p = await createProject(name.trim(), desc.trim());
      nav(`/projects/${p.id}`);
    } catch (err) {
      setError('Errore nella creazione del progetto');
    } finally {
      setCreating(false);
    }
  }

  const totalProjects = projects.length;
  const recentProjects = projects.filter(p => {
    const created = new Date(p.created_at);
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    return created > weekAgo;
  }).length;
  const lastProject = projects[0] || null;

  return (
    <div className="content page-shell">
      <section className="hero">
        <div className="hero__main">
          <span className="hero__eyebrow">DAREEDA Workspace</span>
          <h1 className="hero__title">
            Costruisci workspace EDA con output executive, tecnici e deliverable finali in un unico flusso.
          </h1>
          <p className="hero__lede">
            Il frontend ora segue il linguaggio del file allegato: topbar editoriale, pannelli chiari,
            accento rosso e una struttura da control room per orchestrare ogni analisi.
          </p>
          <div className="hero__actions">
            <a className="btn btn--primary btn--lg" href="#new-project">Nuovo workspace</a>
            <p className="hero__hint">
              Ogni progetto diventa il contenitore di dataset, configurazioni e output enterprise.
            </p>
          </div>
        </div>

        <div className="hero__rail">
          <div className="hero-stat">
            <span className="hero-stat__label">Workspace attivi</span>
            <strong className="hero-stat__value">{totalProjects}</strong>
            <span className="hero-stat__meta">registry centrale</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Creati negli ultimi 7 giorni</span>
            <strong className="hero-stat__value">{recentProjects}</strong>
            <span className="hero-stat__meta">nuovi ingressi</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Ultimo aggiornamento</span>
            <strong className="hero-stat__value">
              {lastProject ? formatProjectDate(lastProject.created_at) : 'N/A'}
            </strong>
            <span className="hero-stat__meta">
              {lastProject ? lastProject.name : 'nessun progetto creato'}
            </span>
          </div>
        </div>
      </section>

      {projectsError && (
        <div className="alert alert--error u-mb-4" role="alert">
          <span>Caricamento progetti non riuscito.</span>
          <span>{projectsError}</span>
        </div>
      )}

      {!loadingProjects && totalProjects > 0 && (
        <div className="metrics-strip" role="region" aria-label="Statistiche progetti">
          <StatCard label="Totale Progetti" value={totalProjects} />
          <StatCard
            label="Nuovi (7gg)"
            value={recentProjects}
            trend={recentProjects > 0 ? Math.round((recentProjects / totalProjects) * 100) : 0}
          />
          <StatCard label="Attività" value="Attivo" accent={true} />
        </div>
      )}

      <div className="workspace-grid">
        <section className="card card--accent" aria-label="Crea nuovo progetto" id="new-project">
          <div className="card__header">
            <div className="card__header-left">
              <span className="card__eyebrow">Workspace Creation</span>
              <h2 className="card__title">Apri un nuovo progetto operativo</h2>
              <p className="card__subtitle">
                Definisci nome e descrizione del workspace. Da qui partiranno upload, configurazione
                analisi e produzione di tutti gli output del report enterprise.
              </p>
            </div>
          </div>

          <form onSubmit={handleCreate} className="panel-form">
            <div className="panel-form__grid">
              <div className="form-group">
                <label htmlFor="project-name" className="form-label">Nome progetto</label>
                <input
                  id="project-name"
                  className="form-input"
                  placeholder="es. Analisi Vendite Q1"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  required
                  aria-required="true"
                  maxLength={100}
                />
              </div>
              <div className="form-group">
                <label htmlFor="project-desc" className="form-label">Descrizione</label>
                <input
                  id="project-desc"
                  className="form-input"
                  placeholder="Breve descrizione operativa"
                  value={desc}
                  onChange={e => setDesc(e.target.value)}
                  maxLength={255}
                />
              </div>
            </div>

            {error && (
              <div className="alert alert--error" role="alert">
                <span>Errore.</span>
                <span>{error}</span>
              </div>
            )}

            <div className="panel-form__footer">
              <p className="panel-note">
                Usa nomi chiari: questo titolo verra ripreso in workspace, export e reportistica.
              </p>
              <button
                className="btn btn--primary btn--lg"
                type="submit"
                disabled={creating || !name.trim()}
                aria-busy={creating}
              >
                {creating ? (
                  <>
                    <Spinner size={16} />
                    <span>Creazione...</span>
                  </>
                ) : (
                  <span>Apri workspace</span>
                )}
              </button>
            </div>
          </form>
        </section>

        <aside className="rail-stack">
          <div className="card">
            <div className="card__header">
              <div className="card__header-left">
                <span className="card__eyebrow">Operating Model</span>
                <h2 className="card__title">Come leggere il workspace</h2>
              </div>
            </div>
            <div className="stack-list">
              <div className="stack-list__item">
                <span className="stack-list__index">01</span>
                <p>Apri un progetto e usalo come contenitore stabile per dataset e analisi.</p>
              </div>
              <div className="stack-list__item">
                <span className="stack-list__index">02</span>
                <p>Configura target, feature e run nel canvas di upload ispirato al file allegato.</p>
              </div>
              <div className="stack-list__item">
                <span className="stack-list__index">03</span>
                <p>Consulta output executive, EDA, governance e deliverable senza cambiare ambiente.</p>
              </div>
            </div>
          </div>

          <div className="card card--muted">
            <div className="card__header">
              <div className="card__header-left">
                <span className="card__eyebrow">Readiness Snapshot</span>
                <h2 className="card__title">Stato del registry</h2>
              </div>
            </div>
            <div className="meta-list">
              <div className="meta-list__row">
                <span>Workspace presenti</span>
                <strong>{totalProjects}</strong>
              </div>
              <div className="meta-list__row">
                <span>Ultimi 7 giorni</span>
                <strong>{recentProjects}</strong>
              </div>
              <div className="meta-list__row">
                <span>Ultimo creato</span>
                <strong>{lastProject ? lastProject.name : 'N/A'}</strong>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <section className="section-shell">
        <div className="section-shell__header">
          <div>
            <span className="section-shell__eyebrow">Project Registry</span>
            <h2 className="section-shell__title">Workspace attivi</h2>
            <p className="section-shell__subtitle">
              Ogni card apre un workspace operativo con dataset, upload e configurazione analitica.
            </p>
          </div>
        </div>

        {loadingProjects ? (
          <div className="empty-state" role="status" aria-label="Caricamento progetti">
            <Spinner size={48} />
            <p className="u-mt-4 u-text-secondary">Caricamento progetti...</p>
          </div>
        ) : totalProjects === 0 ? (
          <div className="empty-state" role="status">
            <div className="empty-state__icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="3" width="7" height="7" rx="1" opacity="0.3" />
                <rect x="14" y="3" width="7" height="7" rx="1" opacity="0.5" />
                <rect x="14" y="14" width="7" height="7" rx="1" opacity="0.7" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
              </svg>
            </div>
            <h3 className="empty-state__title">Nessun progetto</h3>
            <p className="empty-state__description">
              Inizia creando il primo workspace. Da li potrai caricare dataset, configurare target
              e generare tutti gli output dell'analisi.
            </p>
          </div>
        ) : (
          <div className="card-grid" role="list" aria-label="Lista progetti">
            {projects.map(project => (
              <article
                key={project.id}
                className="project-card"
                onClick={() => nav(`/projects/${project.id}`)}
                role="listitem"
                tabIndex={0}
                onKeyDown={(event) => event.key === 'Enter' && nav(`/projects/${project.id}`)}
                aria-label={`Progetto ${project.name}`}
              >
                <div className="project-card__header">
                  <span className="project-card__icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M4 6.5h16v11H4z" />
                      <path d="M8 6.5V5a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v1.5" />
                    </svg>
                  </span>
                  <div>
                    <div className="project-card__name">{project.name}</div>
                    <div className="project-card__meta">Workspace operativo</div>
                  </div>
                </div>

                {project.description ? (
                  <p className="project-card__desc">{project.description}</p>
                ) : (
                  <p className="project-card__desc project-card__desc--empty">Nessuna descrizione</p>
                )}

                <div className="project-card__footer">
                  <time className="project-card__date" dateTime={project.created_at}>
                    {formatProjectDate(project.created_at)}
                  </time>
                  <span className="project-card__arrow" aria-hidden="true">Open</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default HomePage;
