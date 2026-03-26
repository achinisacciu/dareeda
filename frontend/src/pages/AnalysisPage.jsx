import { useEffect, useMemo, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { Spinner, SpinnerAccent } from '../components/Spinner';
import { ProgressBar } from '../components/ProgressBar';
import { OverviewSection }    from '../components/eda/OverviewSection';
import { ExecutiveSection }   from '../components/eda/ExecutiveSection';
import { ProfilingSection }   from '../components/eda/ProfilingSection';
import { DataQualitySection } from '../components/eda/DataQualitySection';
import { UnivariateSection }  from '../components/eda/UnivariateSection';
import { BivariateSection }   from '../components/eda/BivariateSection';
import { MultivariateSection } from '../components/eda/MultivariateSection';
import { TimeSeriesSection }  from '../components/eda/TimeSeriesSection';
import { MLSection }          from '../components/eda/MLSection';
import { InferenceSection }   from '../components/eda/InferenceSection';
import { CleaningSection }    from '../components/eda/CleaningSection';
import { PredictivePrepSection } from '../components/eda/PredictivePrepSection';
import { AdvancedAnalyticsSection } from '../components/eda/AdvancedAnalyticsSection';
import { GovernanceSection } from '../components/eda/GovernanceSection';
import { DeliverablesSection } from '../components/eda/DeliverablesSection';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { reportsApi } from '../api/client';

const ALL_SECTIONS = [
  { key: 'executive',      label: 'Executive',    icon: '◆', Component: ExecutiveSection },
  { key: 'overview',       label: 'Panoramica',   icon: '◈', Component: OverviewSection },
  { key: 'profiling',      label: 'Profiling',    icon: '▣', Component: ProfilingSection },
  { key: 'data_quality',   label: 'Qualità dati', icon: '◎', Component: DataQualitySection },
  { key: 'cleaning',       label: 'Pulizia',     icon: '✂', Component: CleaningSection },
  { key: 'univariate',     label: 'Univariata',   icon: '◉', Component: UnivariateSection },
  { key: 'bivariate',      label: 'Bivariata',    icon: '◈', Component: BivariateSection },
  { key: 'multivariate',   label: 'Multivariata', icon: '⬡', Component: MultivariateSection },
  { key: 'timeseries',     label: 'Time Series',  icon: '◷', Component: TimeSeriesSection },
  { key: 'ml_exploratory', label: 'ML Esplor.',   icon: '◎', Component: MLSection },
  { key: 'inference',      label: 'Inferenza',    icon: '◈', Component: InferenceSection },
  { key: 'predictive_prep', label: 'ML Prep',     icon: '⬢', Component: PredictivePrepSection },
  { key: 'advanced_analytics', label: 'Advanced', icon: '◬', Component: AdvancedAnalyticsSection },
  { key: 'governance',     label: 'Governance',   icon: '⚖', Component: GovernanceSection },
  { key: 'deliverables',   label: 'Output',       icon: '▤', Component: DeliverablesSection },
];

export function AnalysisPage() {
  const { analysisId } = useParams();
  const { analysisStatus, analysisResults, pollStatus, stopPolling } = useStore();
  const storageKey = `dareeda-analysis-tab:${analysisId}`;
  const [activeKey, setActiveKey] = useState(() => sessionStorage.getItem(storageKey) || 'overview');
  const [rep, setRep] = useState({ status: 'idle', id: null });
  const contentRef = useRef(null);

  useDocumentTitle(analysisStatus?.status === 'running' ? 'Analisi in corso' : 'Analisi EDA');

  useEffect(() => { pollStatus(analysisId); return () => stopPolling(); }, [analysisId]);

  useEffect(() => {
    if (contentRef.current) contentRef.current.scrollTop = 0;
  }, [activeKey]);

  useEffect(() => {
    sessionStorage.setItem(storageKey, activeKey);
  }, [activeKey, storageKey]);

  useEffect(() => {
    if (rep.status !== 'pending') return;
    const iv = setInterval(async () => {
      try {
        const { data } = await reportsApi.status(rep.id);
        setRep(r => ({ ...r, status: data.status }));
        if (data.status !== 'pending') clearInterval(iv);
      } catch { clearInterval(iv); }
    }, 2000);
    return () => clearInterval(iv);
  }, [rep.id, rep.status]);

  const startReport = async () => {
    setRep({ status: 'pending', id: null });
    try {
      const { data } = await reportsApi.generate(analysisId);
      setRep({ status: 'pending', id: data.report_id });
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Errore';
      setRep({ status: 'failed', id: null, msg });
    }
  };

  const status = analysisStatus?.status;
  const isBootstrapping = !analysisStatus && !analysisResults;
  const isResolvingResults = status === 'completed' && !analysisResults;
  const sections = useMemo(() => {
    return analysisResults
      ? ALL_SECTIONS.filter(s => {
          if (s.key === 'cleaning') {
            const hasIssues = (analysisResults?.data_quality?.standardized_issues || []).length > 0;
            const hasAppliedCleaning = (analysisResults?.applied_cleaning?.actions || []).length > 0;
            return hasIssues || hasAppliedCleaning;
          }
          return analysisResults[s.key] && !analysisResults[s.key].skipped;
        })
      : [];
  }, [analysisResults]);

  const currentKey = useMemo(() => {
    return sections.find(s => s.key === activeKey)?.key || sections[0]?.key || 'overview';
  }, [sections, activeKey]);

  const ActiveSection = useMemo(
    () => sections.find(s => s.key === currentKey)?.Component,
    [sections, currentKey],
  );

  const activeData =
    currentKey === 'cleaning' || currentKey === 'deliverables'
      ? analysisResults
      : analysisResults?.[currentKey];
  const activeSection = useMemo(
    () => sections.find(s => s.key === currentKey),
    [sections, currentKey],
  );
  const reportStatusLabel = rep.status === 'completed'
    ? 'PDF ready'
    : rep.status === 'pending'
      ? 'Generating'
      : rep.status === 'failed'
        ? 'Failed'
        : 'Idle';

  return (
    <div className="content page-shell analysis-page">
      <section className="hero">
        <div className="hero__main">
          <nav className="topbar__breadcrumb u-mb-2" aria-label="Breadcrumb">
            <Link to="/">Progetti</Link>
            <span className="topbar__breadcrumb-separator">/</span>
            <span aria-current="page">Analisi</span>
          </nav>
          <span className="hero__eyebrow">EDA Control Room</span>
          <h1 className="hero__title">Analisi EDA</h1>
          <p className="hero__lede">
            Canvas operativo per leggere sezioni executive, profiling, qualita dati, multivariata,
            ML prep, governance e deliverable finali.
          </p>
          <p className="hero__meta">{analysisId}</p>
        </div>

        <div className="hero__rail">
          <div className="hero-stat">
            <span className="hero-stat__label">Status</span>
            <strong className="hero-stat__value">{status || 'Booting'}</strong>
            <span className="hero-stat__meta">{analysisStatus?.current_module || 'pipeline orchestration'}</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Available outputs</span>
            <strong className="hero-stat__value">{sections.length}</strong>
            <span className="hero-stat__meta">sections rendered</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Report package</span>
            <strong className="hero-stat__value">{reportStatusLabel}</strong>
            <span className="hero-stat__meta">pdf generation state</span>
          </div>
        </div>
      </section>

      {status === 'completed' && (
        <div className="toolbar-row">
          {rep.status === 'idle' && (
            <button className="btn btn--secondary" onClick={startReport}>
              Genera PDF
            </button>
          )}
          {rep.status === 'pending' && (
            <button className="btn btn--secondary" disabled>
              <Spinner size={14} />
              <span>Generazione...</span>
            </button>
          )}
          {rep.status === 'completed' && (
            <a
              className="btn btn--primary"
              href={reportsApi.downloadUrl(rep.id)}
              target="_blank"
              rel="noreferrer"
            >
              Scarica PDF
            </a>
          )}
          {rep.status === 'failed' && (
            <div className="u-text-right">
              <span className="badge badge--error">PDF non disponibile</span>
              <p className="u-text-muted u-mt-1" style={{ fontSize: '0.75rem' }}>
                {rep.msg || 'Controlla il backend'}
              </p>
            </div>
          )}
        </div>
      )}

      {(isBootstrapping || status === 'pending' || status === 'running' || isResolvingResults) && (
        <div className="card u-mb-6">
          <div className="analysis-loading-state u-p-8">
              <SpinnerAccent size={44} />
              <p className="u-text-secondary u-text-sm">
                {isBootstrapping
                  ? 'Connessione allo stato analisi...'
                  : isResolvingResults
                    ? 'Caricamento risultati analisi...'
                    : (analysisStatus?.current_module || 'Inizializzazione...')}
              </p>
            <div className="u-w-full" style={{ maxWidth: 400 }}>
              <ProgressBar pct={analysisStatus?.progress_pct || 0} />
            </div>
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div className="alert alert--error" role="alert">
          <span>Analisi fallita.</span>
          <span>{analysisStatus?.error_message}</span>
        </div>
      )}

      {status === 'completed' && analysisResults && sections.length > 0 && (
        <div className="analysis-body">
          <div className="tabs__nav analysis-tabs" role="tablist">
            {sections.map(s => (
              <button
                key={s.key}
                role="tab"
                aria-selected={currentKey === s.key}
                className={`tab${currentKey === s.key ? ' tab--active' : ''}`}
                onClick={() => setActiveKey(s.key)}
              >
                <span className="tab__icon" aria-hidden="true">{s.icon}</span>
                <span className="tab__label">{s.label}</span>
              </button>
            ))}
          </div>

          <div className="analysis-stage">
            <div className="analysis-stage__header">
              <div>
                <span className="analysis-stage__eyebrow">Current Output</span>
                <h2 className="analysis-stage__title">{activeSection?.label}</h2>
              </div>
              <span className="badge badge--neutral">{currentKey}</span>
            </div>

            <div className="analysis-content" ref={contentRef}>
            {ActiveSection && activeData && (
              <div className="eda-section">
                <div className="eda-section__header">
                  <span className="eda-section__icon" aria-hidden="true">
                    {activeSection?.icon}
                  </span>
                  <h2 className="eda-section__title">{activeSection?.label}</h2>
                </div>
                <ActiveSection data={activeData} analysisId={analysisResults?.analysis_id} />
              </div>
            )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default AnalysisPage;
