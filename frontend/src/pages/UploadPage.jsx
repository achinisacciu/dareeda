import { useState, useCallback, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { analysisApi } from '../api/client';
import { Spinner } from '../components/Spinner';
import { StatCard } from '../components/StatCard';
import { ProgressBar } from '../components/ProgressBar';
import { SuggestedFeaturesPanel } from '../components/upload/SuggestedFeaturesPanel';
import { LoadingOverlay } from '../components/LoadingOverlay';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

const SEMANTIC_COLORS = {
  numeric_continuous: '#59ADF7', numeric_discrete: '#0904AE',
  categorical_nominal: '#1B272F', categorical_ordinal: '#37424A',
  boolean: '#112F44', datetime: '#0904AE', text: '#E4002B',
  id: '#6B7280', geographic: '#112F44', unknown: '#B8B0A8',
};

function inferProblemType(semanticType) {
  if (semanticType === 'numeric_continuous') return 'regression';
  if (
    semanticType === 'numeric_discrete' ||
    semanticType === 'categorical_nominal' ||
    semanticType === 'categorical_ordinal' ||
    semanticType === 'boolean'
  ) {
    return 'classification';
  }
  return '';
}

function extractErrorMessage(e) {
  const detail = e?.response?.data?.detail;
  if (!detail) return 'Errore sconosciuto.';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => `${d.loc?.join('.')}: ${d.msg}`).join(' | ');
  }
  if (typeof detail === 'object') return JSON.stringify(detail);
  return String(detail);
}

function formatTechnicalType(dtypeOriginal, semanticType) {
  const dt = String(dtypeOriginal || '').toLowerCase();
  // Preferisci semantica quando è chiaro (es. categorie/testo)
  if (semanticType === 'id') return 'ID / quasi-ID';
  if (semanticType === 'datetime') return 'Datetime';
  if (semanticType === 'boolean') return 'Booleano';

  if (semanticType === 'categorical_nominal' || semanticType === 'categorical_ordinal') return 'Categorico';
  if (semanticType === 'text') return 'Testo';

  if (dt.includes('int') || dt.includes('uint')) return 'Numerico (intero)';
  if (dt.includes('float') || dt.includes('decimal')) return 'Numerico (reale)';
  if (dt.includes('bool')) return 'Booleano';
  if (dt.includes('datetime') || dt.includes('date')) return 'Datetime';
  if (dt.includes('utf8') || dt.includes('string')) return 'Testo';

  return dtypeOriginal ? String(dtypeOriginal) : 'Sconosciuto';
}

function waitNextPaint() {
  return new Promise(resolve => {
    window.requestAnimationFrame(() => resolve());
  });
}

export function UploadPage() {
  const { projectId } = useParams();
  const nav = useNavigate();
  const { uploadDataset, uploadProgress, uploadResult } = useStore();
  const [dragging, setDragging]           = useState(false);
  const [uploading, setUploading]         = useState(false);
  const [error, setError]                 = useState(null);
  const [starting, setStarting]           = useState(false);
  const [finalFeatures, setFinalFeatures] = useState(null);
  const [targetColumn, setTargetColumn]   = useState('');
  const [problemType, setProblemType]     = useState('');

  useDocumentTitle('Carica Dataset');

  const handleFile = useCallback(async (file) => {
    setError(null);
    setUploading(true);
    setFinalFeatures(null);
    try {
      await uploadDataset(file, projectId);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally { setUploading(false); }
  }, [projectId]);

  const onDrop = useCallback(e => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onFileChange = e => { if (e.target.files[0]) handleFile(e.target.files[0]); };

  const availableColumns = uploadResult?.columns || [];

  useEffect(() => {
    setTargetColumn('');
    setProblemType('');
  }, [uploadResult?.dataset_id]);

  useEffect(() => {
    if (!targetColumn) {
      setProblemType('');
      return;
    }

    const selectedTarget = availableColumns.find(col => col.name === targetColumn);
    if (!selectedTarget) {
      setProblemType('');
      return;
    }

    const inferred = inferProblemType(selectedTarget.semantic_type);
    setProblemType(prev => prev || inferred);
  }, [targetColumn, availableColumns]);

  const startAnalysis = async () => {
    if (!uploadResult) return;
    setStarting(true);
    setError(null);
    try {
      await waitNextPaint();
      const acceptedFeatures = (finalFeatures || uploadResult.suggested_features || [])
        .filter(f => f.status === 'accepted')
        .map(f => f.name);

      const { data } = await analysisApi.run(uploadResult.dataset_id, {
        accepted_features: acceptedFeatures,
        target: targetColumn || null,
        problem_type: targetColumn ? (problemType || null) : null,
      });
      nav(`/analysis/${data.analysis_id}`);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally { setStarting(false); }
  };

  const suggestedFeatures = uploadResult?.suggested_features || [];
  const acceptedCount = (finalFeatures || suggestedFeatures)
    .filter(f => f.status === 'accepted').length;
  const semanticCoverage = availableColumns.length
    ? Math.round((availableColumns.filter(col => col.semantic_type && col.semantic_type !== 'unknown').length / availableColumns.length) * 100)
    : 0;
  const selectedTarget = availableColumns.find(col => col.name === targetColumn);

  return (
    <div className={`content page-shell${starting ? ' page-busy' : ''}`}>
      <LoadingOverlay
        open={starting}
        title="Analisi in avvio"
        description="Stiamo preparando la nuova esecuzione EDA con la configurazione selezionata."
      />
      <section className="hero">
        <div className="hero__main">
          <nav className="topbar__breadcrumb" aria-label="Breadcrumb">
            <Link to="/">Progetti</Link>
            <span className="topbar__breadcrumb-separator">/</span>
            <Link to={`/projects/${projectId}`}>Progetto</Link>
            <span className="topbar__breadcrumb-separator">/</span>
            <span aria-current="page">Carica</span>
          </nav>
          <span className="hero__eyebrow">Analysis Configuration</span>
          <h1 className="hero__title">Carica dataset e orchestra la nuova run</h1>
          <p className="hero__lede">
            La pagina segue il modello del file allegato: intake chiaro, controllo dei metadati,
            selezione target e configurazione prima dell'avvio dell'EDA completa.
          </p>
        </div>

        <div className="hero__rail">
          <div className="hero-stat">
            <span className="hero-stat__label">Formati supportati</span>
            <strong className="hero-stat__value">CSV</strong>
            <span className="hero-stat__meta">XLSX e JSON inclusi</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Target configurato</span>
            <strong className="hero-stat__value">{targetColumn || 'EDA only'}</strong>
            <span className="hero-stat__meta">{problemType || 'no supervised target'}</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat__label">Feature accettate</span>
            <strong className="hero-stat__value">{acceptedCount}</strong>
            <span className="hero-stat__meta">dal pannello suggerimenti</span>
          </div>
        </div>
      </section>

      {!uploadResult && (
        <div className="workspace-grid workspace-grid--upload">
          <div
            className={`dropzone dropzone--feature${dragging ? ' dropzone--active' : ''}`}
            onDrop={onDrop}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
          >
            {uploading ? (
              <div className="u-flex u-flex-col u-items-center u-gap-4">
                <Spinner size={32} />
                <p className="u-text-secondary u-text-sm">Caricamento in corso...</p>
                <ProgressBar pct={uploadProgress} />
              </div>
            ) : (
              <div className="dropzone__content">
                <span className="dropzone__eyebrow">Dataset Intake</span>
                <h2 className="dropzone__title">Trascina il file nel canvas oppure selezionalo manualmente.</h2>
                <p className="dropzone__description">
                  Il sistema rileva schema, tipologie semantiche, target candidati e feature suggerite
                  prima dell'avvio della run.
                </p>
                <div className="dropzone__actions">
                  <label className="btn btn--primary btn--lg">
                    Seleziona file
                    <input type="file" accept=".csv,.xlsx,.json" hidden onChange={onFileChange} />
                  </label>
                  <span className="dropzone__formats">CSV, XLSX, JSON</span>
                </div>
              </div>
            )}
          </div>

          <aside className="rail-stack">
            <div className="card">
              <div className="card__header">
                <div className="card__header-left">
                  <span className="card__eyebrow">Expected Outputs</span>
                  <h2 className="card__title">Cosa viene preparato</h2>
                </div>
              </div>
              <div className="stack-list">
                <div className="stack-list__item">
                  <span className="stack-list__index">01</span>
                  <p>Profiling strutturale, quality engine e rilevamento tipologie semantiche.</p>
                </div>
                <div className="stack-list__item">
                  <span className="stack-list__index">02</span>
                  <p>Target setup, feature selection e impostazione della problem class.</p>
                </div>
                <div className="stack-list__item">
                  <span className="stack-list__index">03</span>
                  <p>Run EDA completa con output executive, tecnici, governance e deliverables.</p>
                </div>
              </div>
            </div>

            <div className="card card--muted">
              <div className="card__header">
                <div className="card__header-left">
                  <span className="card__eyebrow">Upload Notes</span>
                  <h2 className="card__title">Vincoli operativi</h2>
                </div>
              </div>
              <div className="meta-list">
                <div className="meta-list__row">
                  <span>Formati</span>
                  <strong>CSV / XLSX / JSON</strong>
                </div>
                <div className="meta-list__row">
                  <span>Target</span>
                  <strong>Facoltativa</strong>
                </div>
                <div className="meta-list__row">
                  <span>Avvio run</span>
                  <strong>Manuale dopo review</strong>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}

      {error && (
        <div className="alert alert--error u-mt-4" role="alert">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {uploadResult && (
        <div className="u-flex u-flex-col u-gap-6">
          <div className="metrics-strip" role="region" aria-label="Riepilogo dataset">
            <StatCard label="Righe"      value={uploadResult.n_rows.toLocaleString('it-IT')} />
            <StatCard label="Colonne"    value={uploadResult.n_cols} />
            <StatCard label="Memoria"    value={uploadResult.memory_mb} unit="MB" />
            <StatCard label="Campionato" value={uploadResult.sampled ? 'Sì' : 'No'} accent={uploadResult.sampled} />
          </div>

          <div className="workspace-grid workspace-grid--upload-results">
            <div className="u-flex u-flex-col u-gap-6">
              {suggestedFeatures.length > 0 && (
                <SuggestedFeaturesPanel
                  datasetId={uploadResult.dataset_id}
                  features={suggestedFeatures}
                  onDecisionsChange={setFinalFeatures}
                />
              )}

              {availableColumns.length > 0 && (
                <div className="card">
                  <div className="card__header">
                    <div className="card__header-left">
                      <span className="card__eyebrow">Target Mapping</span>
                      <h2 className="card__title">Target e tipo problema</h2>
                      <p className="card__subtitle">
                        Puoi scegliere la target tra tutte le colonne disponibili. Se il tipo non e
                        inferibile automaticamente, impostalo manualmente.
                      </p>
                    </div>
                  </div>

                  <div className="panel-form__grid">
                    <div className="form-group">
                      <label className="form-label" htmlFor="target-column">Colonna target</label>
                      <select
                        id="target-column"
                        className="form-select"
                        value={targetColumn}
                        onChange={e => setTargetColumn(e.target.value)}
                        disabled={starting}
                      >
                        <option value="">Nessuna target</option>
                        {availableColumns.map(col => (
                          <option key={col.name} value={col.name}>
                            {col.name} ({col.semantic_type})
                          </option>
                        ))}
                      </select>
                      <p className="form-hint">
                        Tutte le colonne sono selezionabili come target. La semantica serve solo per suggerire
                        il tipo di problema.
                      </p>
                    </div>

                    <div className="form-group">
                      <label className="form-label" htmlFor="problem-type">Tipo di problema</label>
                      <select
                        id="problem-type"
                        className="form-select"
                        value={problemType}
                        onChange={e => setProblemType(e.target.value)}
                        disabled={!targetColumn || starting}
                      >
                        <option value="">Seleziona tipo</option>
                        <option value="classification">Classification</option>
                        <option value="regression">Regression</option>
                      </select>
                      <p className="form-hint">
                        Suggerito automaticamente quando possibile, ma sempre modificabile.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="card">
                <div className="card__header">
                  <div className="card__header-left">
                    <span className="card__eyebrow">Schema Registry</span>
                    <h2 className="card__title">Colonne rilevate</h2>
                    <p className="card__subtitle">{uploadResult.columns.length} colonne trovate</p>
                  </div>
                </div>
                <div className="table-container">
                  <table className="table" aria-label="Colonne del dataset">
                    <thead>
                      <tr>
                        <th>Nome</th>
                        <th>Tipo semantico</th>
                        <th>Tipo reale</th>
                        <th className="numeric">Unici</th>
                        <th className="numeric">Missing %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uploadResult.columns.map(c => (
                        <tr key={c.name}>
                          <td className="u-font-medium">{c.name}</td>
                          <td>
                            <span
                              className="badge badge--neutral"
                              style={{ color: SEMANTIC_COLORS[c.semantic_type] || '#888' }}
                            >
                              {c.semantic_type}
                            </span>
                          </td>
                          <td>
                            <span className="badge badge--neutral">
                              {formatTechnicalType(c.dtype_original, c.semantic_type)}
                            </span>
                          </td>
                          <td className="numeric">{c.n_unique}</td>
                          <td className="numeric">{c.pct_missing}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="panel-callout">
                <div>
                  <span className="panel-callout__label">Run Launch</span>
                  {acceptedCount > 0 && (
                    <p className="panel-callout__text">
                      {acceptedCount} misure verranno incluse nell'analisi.
                    </p>
                  )}
                </div>
                <button
                  className="btn btn--primary btn--lg"
                  onClick={startAnalysis}
                  disabled={starting}
                  aria-busy={starting}
                >
                  {starting
                    ? <><Spinner size={16} /><span>Avvio analisi...</span></>
                    : <span>Avvia analisi EDA completa</span>
                  }
                </button>
              </div>
            </div>

            <aside className="rail-stack">
              <div className="card">
                <div className="card__header">
                  <div className="card__header-left">
                    <span className="card__eyebrow">Readiness Snapshot</span>
                    <h2 className="card__title">Stato dataset</h2>
                  </div>
                </div>
                <div className="meta-list">
                  <div className="meta-list__row">
                    <span>Semantic coverage</span>
                    <strong>{semanticCoverage}%</strong>
                  </div>
                  <div className="meta-list__row">
                    <span>Target</span>
                    <strong>{selectedTarget ? selectedTarget.name : 'EDA only'}</strong>
                  </div>
                  <div className="meta-list__row">
                    <span>Problem type</span>
                    <strong>{problemType || 'Not set'}</strong>
                  </div>
                </div>
              </div>

              <div className="card card--muted">
                <div className="card__header">
                  <div className="card__header-left">
                    <span className="card__eyebrow">Execution Notes</span>
                    <h2 className="card__title">Prima del lancio</h2>
                  </div>
                </div>
                <div className="stack-list">
                  <div className="stack-list__item">
                    <span className="stack-list__index">A</span>
                    <p>Conferma target e tipo problema se vuoi attivare i blocchi supervised.</p>
                  </div>
                  <div className="stack-list__item">
                    <span className="stack-list__index">B</span>
                    <p>Rivedi le feature suggerite: quelle accettate saranno incluse nella run.</p>
                  </div>
                  <div className="stack-list__item">
                    <span className="stack-list__index">C</span>
                    <p>La nuova run aprira il canvas analitico con tutte le sezioni disponibili.</p>
                  </div>
                </div>
              </div>
            </aside>
          </div>

        </div>
      )}
    </div>
  );
}

export default UploadPage;
