import { useEffect, useState } from 'react';
import { datasetsApi } from '../../api/client';

const TYPE_LABELS = {
  revenue:    { label: 'Ricavo',   badge: 'badge--success' },
  margin:     { label: 'Margine',  badge: 'badge--info' },
  margin_pct: { label: 'Margine %', badge: 'badge--info' },
  ratio:      { label: 'Rapporto', badge: 'badge--neutral' },
  discount:   { label: 'Sconto',   badge: 'badge--warning' },
};

const CONFIDENCE_COLOR = (conf) => {
  if (conf >= 0.85) return 'u-text-success';
  if (conf >= 0.65) return 'u-text-warning';
  return 'u-text-muted';
};

export function SuggestedFeaturesPanel({ datasetId, features: initialFeatures, onDecisionsChange }) {
  const [features, setFeatures] = useState(
    (initialFeatures || []).map(f => ({ ...f, status: f.status || 'pending' }))
  );
  const [saving, setSaving] = useState(false);
  const [savedOk, setSavedOk] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setFeatures((initialFeatures || []).map(f => ({ ...f, status: f.status || 'pending' })));
  }, [initialFeatures]);

  useEffect(() => {
    if (onDecisionsChange) onDecisionsChange(features);
  }, [features, onDecisionsChange]);

  if (!features || features.length === 0) return null;

  const pending  = features.filter(f => f.status === 'pending').length;
  const accepted = features.filter(f => f.status === 'accepted').length;
  const rejected = features.filter(f => f.status === 'rejected').length;

  // Cambia status di una singola misura localmente
  function toggleFeature(name, newStatus) {
    setFeatures(prev => prev.map(f => (f.name === name ? { ...f, status: newStatus } : f)));
  }

  // Accetta/rifiuta tutto localmente
  function setAll(status) {
    setFeatures(prev => prev.map(f => ({ ...f, status })));
  }

  // Salva le decisioni sul backend
  async function saveDecisions() {
    setSaving(true);
    setError(null);
    setSavedOk(false);
    try {
      const decisions = features.map(f => ({ name: f.name, status: f.status }));
      await datasetsApi.updateFeatureDecisions(datasetId, decisions);
      setSavedOk(true);
      // Mostra feedback per qualche secondo
      setTimeout(() => setSavedOk(false), 6000);
    } catch (e) {
      const detail = e?.response?.data?.detail || e?.message || 'Errore nel salvataggio delle decisioni.';
      setError(String(detail));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card u-mb-6">
      <div className="card__header">
        <div className="card__header-left">
          <h2 className="card__title">Misure suggerite</h2>
          <p className="card__subtitle">
            Il sistema ha rilevato {features.length} misure derivabili dai tuoi dati.
            Scegli quali includere nell&apos;analisi.
          </p>
        </div>
        <div className="card__header-right">
          {pending > 0 && (
            <span className="badge badge--warning">
              <span className="badge__dot" />
              {pending} da decidere
            </span>
          )}
          {accepted > 0 && (
            <span className="badge badge--success">{accepted} accettate</span>
          )}
          {rejected > 0 && (
            <span className="badge badge--neutral">{rejected} rifiutate</span>
          )}
        </div>
      </div>

      {/* Azioni globali */}
      <div className="u-flex u-gap-2 u-mb-4">
        <button className="btn btn--secondary btn--sm" onClick={() => setAll('accepted')}>
          ✓ Accetta tutte
        </button>
        <button className="btn btn--secondary btn--sm" onClick={() => setAll('rejected')}>
          ✕ Rifiuta tutte
        </button>
        <button className="btn btn--secondary btn--sm" onClick={() => setAll('pending')}>
          ↺ Reset
        </button>
      </div>

      {/* Lista misure */}
      <div className="u-flex u-flex-col u-gap-3 u-mb-4">
        {features.map(f => {
          const typeInfo = TYPE_LABELS[f.type] || { label: f.type, badge: 'badge--neutral' };
          const isAccepted = f.status === 'accepted';
          const isRejected = f.status === 'rejected';

          return (
            <div
              key={f.name}
              className={`feature-row${isAccepted ? ' feature-row--accepted' : ''}${isRejected ? ' feature-row--rejected' : ''}`}
            >
              <div className="feature-row__info">
                <div className="u-flex u-items-center u-gap-2 u-mb-1">
                  <span className="u-font-semibold u-text-primary u-text-sm">{f.name}</span>
                  <span className={`badge ${typeInfo.badge}`}>{typeInfo.label}</span>
                  <span className={`u-text-xs u-font-semibold ${CONFIDENCE_COLOR(f.confidence)}`}>
                    {Math.round(f.confidence * 100)}% conf.
                  </span>
                </div>
                <p className="u-text-secondary u-text-sm">{f.description}</p>
                <code className="feature-row__formula">{f.formula}</code>
              </div>

              <div className="feature-row__actions">
                <button
                  className={`btn btn--sm ${isAccepted ? 'btn--primary' : 'btn--secondary'}`}
                  onClick={() => toggleFeature(f.name, isAccepted ? 'pending' : 'accepted')}
                  aria-pressed={isAccepted}
                >
                  ✓
                </button>
                <button
                  className={`btn btn--sm ${isRejected ? 'btn--danger' : 'btn--secondary'}`}
                  onClick={() => toggleFeature(f.name, isRejected ? 'pending' : 'rejected')}
                  aria-pressed={isRejected}
                >
                  ✕
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="alert alert--error u-mb-4" role="alert">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* Salva decisioni */}
      <div className="card__footer">
        <p className="u-text-muted u-text-sm">
          Le misure accettate verranno calcolate e incluse nell&apos;analisi EDA.
        </p>
        <button
          className="btn btn--primary"
          onClick={saveDecisions}
          disabled={saving}
          aria-busy={saving}
        >
          {saving
            ? 'Salvataggio...'
            : savedOk
              ? 'Decisioni salvate ✓'
              : 'Salva decisioni'}
        </button>
      </div>
    </div>
  );
}
