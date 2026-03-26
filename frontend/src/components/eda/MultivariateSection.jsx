import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { PlotlyChart } from '../PlotlyChart';
import { Spinner } from '../Spinner';
import { analysisApi } from '../../api/client';

function makeScatter3DChart({ xCol, yCol, zCol, x, y, z, colorValues, includeTarget }) {
  const marker = {
    size: 4,
    opacity: 0.65,
  };
  if (includeTarget && colorValues) marker.color = colorValues;

  const trace = {
    type: 'scatter3d',
    mode: 'markers',
    name: 'Punti',
    x,
    y,
    z,
    marker,
    hovertemplate: `<b>${xCol}</b>: %{x}<br><b>${yCol}</b>: %{y}<br><b>${zCol}</b>: %{z}<extra></extra>`,
  };

  const layout = {
    title: `Confronto 3 feature: ${xCol}, ${yCol}, ${zCol}`,
    scene: {
      xaxis: { title: xCol },
      yaxis: { title: yCol },
      zaxis: { title: zCol },
    },
    margin: { t: 50, b: 20, l: 10, r: 10 },
  };

  return { data: [trace], layout };
}

function makeParcoordsChart({ dims, colorValues, includeTarget, labels }) {
  const trace = {
    type: 'parcoords',
    dimensions: dims,
    line: includeTarget && colorValues
      ? { color: colorValues, colorscale: 'Viridis', showscale: false }
      : { color: 'rgba(43,43,43,0.7)' },
    // Plotly per parcoords ha un template hover specifico; per evitare placeholder non supportati
    // lasciamo il popup minimal.
    hovertemplate: '<extra></extra>',
  };

  const layout = {
    title: `Confronto 4 feature (parcoords)`,
    margin: { t: 60, b: 20, l: 80, r: 20 },
  };

  return { data: [trace], layout };
}

export function MultivariateSection({ data }) {
  const { analysisId } = useParams();

  const numericColumns = data?.numeric_columns || [];
  const targetColumn = data?.target || null;
  const problemType = data?.problem_type || null;

  const default3 = data?.default_selection_3 || [];
  const default4 = data?.default_selection_4 || [];

  const [mode, setMode] = useState(3);
  const [selected, setSelected] = useState([]);
  const [includeTarget, setIncludeTarget] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleData, setSampleData] = useState(null);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    if (!data) return;
    // Default: 3 feature per velocità
    setMode(3);
    setSelected(default3.slice(0, 3));
    setIncludeTarget(false);
    setSampleData(null);
    setFetchError(null);
  }, [data]);

  useEffect(() => {
    // Se l'utente passa a 4, inizializza con default4 quando possibile.
    if (!data) return;
    if (mode === 4) {
      setSelected(prev => {
        if (prev.length === 4) return prev;
        const seed = default4.slice(0, 4);
        return seed.length === 4 ? seed : prev.slice(0, 4);
      });
    }
    if (mode === 3) {
      setSelected(prev => (prev.length === 3 ? prev : prev.slice(0, 3)));
    }
    setSampleData(null);
    setFetchError(null);
  }, [mode]);

  const targetEnabled = !!targetColumn;
  useEffect(() => {
    if (!targetEnabled && includeTarget) setIncludeTarget(false);
  }, [targetEnabled, includeTarget]);

  const selectedKey = useMemo(() => selected.slice().sort().join('|'), [selected]);

  useEffect(() => {
    if (!analysisId) return;
    if (!data) return;
    if (selected.length !== mode) return;

    let cancelled = false;
    const doFetch = async () => {
      setSampleLoading(true);
      setFetchError(null);
      try {
        const { data: payload } = await analysisApi.sampleData(
          analysisId,
          {
            columns: selected,
            includeTarget: includeTarget && targetEnabled,
          }
        );
        if (cancelled) return;
        setSampleData(payload);
      } catch (e) {
        if (cancelled) return;
        setFetchError('Errore nel caricamento dei dati per Multivariata.');
      } finally {
        if (cancelled) return;
        setSampleLoading(false);
      }
    };

    doFetch();
    return () => { cancelled = true; };
  }, [analysisId, data, selectedKey, includeTarget, targetEnabled, mode]);

  const onToggleFeature = (col) => {
    setSelected(prev => {
      if (prev.includes(col)) return prev.filter(x => x !== col);
      if (prev.length >= mode) return prev; // Limite rigido al numero scelto
      return [...prev, col];
    });
  };

  const xCol = selected[0];
  const yCol = selected[1];
  const zCol = selected[2];
  const targetValues = sampleData?.target?.values || null;

  const scatterChart = useMemo(() => {
    if (!sampleData || mode !== 3 || selected.length !== 3) return null;
    const x = sampleData.columns?.[xCol] || [];
    const y = sampleData.columns?.[yCol] || [];
    const z = sampleData.columns?.[zCol] || [];
    return makeScatter3DChart({
      xCol,
      yCol,
      zCol,
      x,
      y,
      z,
      colorValues: targetValues,
      includeTarget,
    });
  }, [sampleData, mode, selected.length, xCol, yCol, zCol, targetValues, includeTarget]);

  const parcoordsChart = useMemo(() => {
    if (!sampleData || mode !== 4 || selected.length !== 4) return null;
    const dims = selected.map((c) => ({
      label: c,
      values: sampleData.columns?.[c] || [],
    }));
    return makeParcoordsChart({
      dims,
      colorValues: targetValues,
      includeTarget,
      labels: selected,
    });
  }, [sampleData, mode, selected, targetValues, includeTarget]);

  const highPairs = data?.high_correlation_pairs || [];
  const correlationGlobal = data?.correlation_global || {};
  const pca = data?.pca || {};

  if (!numericColumns.length) {
    return (
      <div className="insight">
        <div className="insight__header">Non applicabile</div>
        <div className="insight__content">Nessuna colonna numerica disponibile per Multivariata.</div>
      </div>
    );
  }

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Multivariata</h3>
            <p className="card__subtitle">
              Seleziona 3-4 feature e confrontale con/ senza target.
            </p>
          </div>
        </div>

        <div className="u-flex u-flex-col u-gap-4">
          <div className="u-flex u-gap-4 u-flex-wrap">
            <div className="form-group" style={{ flex: '1 1 280px' }}>
              <label className="form-label">Numero feature</label>
              <select
                className="form-select"
                value={mode}
                onChange={e => setMode(Number(e.target.value))}
              >
                <option value="3">3 feature</option>
                <option value="4">4 feature</option>
              </select>
              <p className="form-hint">Il grafico cambia in base al numero selezionato.</p>
            </div>

            <div className="form-group" style={{ flex: '1 1 280px' }}>
              <label className="form-label">Includi target</label>
              <label className="u-flex u-items-center u-gap-2">
                <input
                  type="checkbox"
                  checked={includeTarget}
                  disabled={!targetEnabled}
                  onChange={e => setIncludeTarget(e.target.checked)}
                />
                <span className="u-text-secondary">
                  {targetEnabled ? targetColumn : 'Nessuna target configurata'}
                </span>
              </label>
              {problemType && (
                <p className="form-hint">Tipo problema: {problemType}</p>
              )}
            </div>
          </div>

          <div className="u-flex u-flex-col u-gap-2">
            <div className="u-text-sm u-text-muted u-mb-1">
              Seleziona {mode} feature numeriche:
            </div>
            <div className="u-flex u-gap-3 u-flex-wrap">
              {numericColumns.map((col) => (
                <label key={col} className="u-flex u-items-center u-gap-2">
                  <input
                    type="checkbox"
                    checked={selected.includes(col)}
                    disabled={!selected.includes(col) && selected.length >= mode}
                    onChange={() => onToggleFeature(col)}
                  />
                  <span className="u-font-medium u-text-sm">{col}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="u-flex u-items-center u-justify-between">
            <p className="u-text-secondary u-text-sm">
              Selezionate: <span className="u-font-semibold">{selected.length}</span> / {mode}
            </p>
            {sampleLoading && (
              <span className="u-flex u-items-center u-gap-2">
                <Spinner size={18} />
                <span className="u-text-secondary u-text-sm">Caricamento dati…</span>
              </span>
            )}
          </div>

          {fetchError && (
            <div className="alert alert--error">
              <span>⚠</span>
              <span>{fetchError}</span>
            </div>
          )}

          {selected.length === mode && !sampleLoading && (
            <div className="charts-grid">
              {mode === 3 && scatterChart && (
                <PlotlyChart chart={scatterChart} height={520} />
              )}
              {mode === 4 && parcoordsChart && (
                <PlotlyChart chart={parcoordsChart} height={520} />
              )}
            </div>
          )}

          {(correlationGlobal?.chart || (pca && !pca.skipped)) && (
            <div className="u-flex u-flex-col u-gap-4">
              {correlationGlobal?.chart && (
                <div className="card">
                  <PlotlyChart chart={correlationGlobal.chart} height={420} />
                </div>
              )}
              {!pca?.skipped && (
                <div className="charts-grid charts-grid--two">
                  {pca?.charts?.scree && <div className="card"><PlotlyChart chart={pca.charts.scree} height={320} /></div>}
                  {pca?.charts?.scatter_pc1_pc2 && <div className="card"><PlotlyChart chart={pca.charts.scatter_pc1_pc2} height={320} /></div>}
                </div>
              )}
            </div>
          )}

          {highPairs.length > 0 && (
            <div className="insight u-mt-2">
              <div className="insight__header">
                <span className="insight__icon">◎</span>
                Coppie ad alta correlazione
              </div>
              <div className="insight__content">
                {highPairs.map(p => (
                  <span key={`${p.var_a}-${p.var_b}`} className="badge badge--error u-mr-2">
                    {p.var_a} x {p.var_b} ({p.correlation})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
