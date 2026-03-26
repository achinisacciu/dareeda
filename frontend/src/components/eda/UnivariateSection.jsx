import { useState } from 'react';
import { PlotlyChart } from '../PlotlyChart';

const TYPE_GROUPS = [
  { key: 'all',     label: 'Tutte' },
  { key: 'numeric', label: 'Numeriche' },
  { key: 'categ',   label: 'Categoriche' },
  { key: 'boolean', label: 'Booleane' },
  { key: 'other',   label: 'Altro' },
];

function getGroup(semantic_type) {
  if (!semantic_type) return 'other';
  if (semantic_type.startsWith('numeric')) return 'numeric';
  if (semantic_type.startsWith('categorical')) return 'categ';
  if (semantic_type === 'boolean') return 'boolean';
  return 'other';
}

export function UnivariateSection({ data }) {
  const cols = Object.keys(data || {});
  const [group, setGroup] = useState('all');
  const [selected, setSelected] = useState(cols[0] || null);

  if (cols.length === 0) return <p className="u-text-secondary">Nessuna colonna analizzata.</p>;

  const filtered = cols.filter(c =>
    group === 'all' || getGroup(data[c]?.semantic_type) === group
  );

  const activeCol = filtered.includes(selected) ? selected : filtered[0] || null;
  const col = activeCol ? data[activeCol] : null;

  const counts = TYPE_GROUPS.reduce((acc, g) => {
    acc[g.key] = g.key === 'all'
      ? cols.length
      : cols.filter(c => getGroup(data[c]?.semantic_type) === g.key).length;
    return acc;
  }, {});

  return (
    <div className="u-flex u-flex-col u-gap-4">

      {/* Filtro gruppi */}
      <div className="tabs__nav" role="tablist">
        {TYPE_GROUPS.filter(g => g.key === 'all' || counts[g.key] > 0).map(g => (
          <button
            key={g.key}
            role="tab"
            aria-selected={group === g.key}
            className={`tab${group === g.key ? ' tab--active' : ''}`}
            onClick={() => setGroup(g.key)}
          >
            {g.label}
            <span className="badge badge--neutral u-ml-2">{counts[g.key]}</span>
          </button>
        ))}
      </div>

      {/* Layout sidebar + contenuto */}
      <div className="uni-layout">
        <aside className="uni-sidebar">
          {filtered.map(c => (
            <button
              key={c}
              className={`uni-col-btn${activeCol === c ? ' uni-col-btn--active' : ''}${data[c]?.error ? ' uni-col-btn--error' : ''}`}
              onClick={() => setSelected(c)}
            >
              <span className="uni-col-name">{c}</span>
              <span className="uni-col-type">{data[c]?.semantic_type}</span>
            </button>
          ))}
        </aside>

        <div className="uni-content">
          {col && <ColDetail name={activeCol} col={col} />}
        </div>
      </div>

    </div>
  );
}

function ColDetail({ name, col }) {
  if (col.error) return (
    <div className="alert alert--error">
      <span>⚠</span>
      <span>{col.error}</span>
    </div>
  );

  if (col.skipped) return (
    <div className="insight">
      <div className="insight__header">Colonna non analizzata</div>
      <div className="insight__content">{col.reason || 'Tipo non supportato'}</div>
    </div>
  );

  const st = col.semantic_type;
  const stats = col.stats || {};
  const charts = col.charts || {};

  return (
    <div className="u-flex u-flex-col u-gap-4">

      {/* Header colonna */}
      <div className="u-flex u-items-center u-gap-3">
        <h3 className="u-text-lg u-font-semibold u-text-primary">{name}</h3>
        <span className="badge badge--neutral">{st}</span>
      </div>

      {/* AI comment */}
      {col.ai_comment && (
        <div className="insight">
          <div className="insight__header">
            <span className="insight__icon">◎</span>
            Osservazione
          </div>
          <div className="insight__content">{col.ai_comment}</div>
        </div>
      )}

      {/* Numerico continuo */}
      {st === 'numeric_continuous' && (
        <>
          <div className="card">
            <div className="table-container">
              <table className="table">
                <tbody>
                  <tr>
                    <th>N (Osservazioni)</th><td>{stats.count?.toLocaleString('it-IT')}</td>
                    <th>Min</th><td>{stats.min}</td>
                  </tr>
                  <tr>
                    <th>Media</th><td>{typeof stats.mean === 'number' ? stats.mean.toFixed(2) : stats.mean}</td>
                    <th>P25 (Q1)</th><td>{stats.q1}</td>
                  </tr>
                  <tr>
                    <th>Mediana</th><td>{stats.median}</td>
                    <th>P75 (Q3)</th><td>{stats.q3}</td>
                  </tr>
                  <tr>
                    <th>Dev. Standard</th><td>{typeof stats.std === 'number' ? stats.std.toFixed(2) : stats.std}</td>
                    <th>Max</th><td>{stats.max}</td>
                  </tr>
                  <tr>
                    <th>Skewness</th>
                    <td className={Math.abs(stats.skewness) > 1 ? 'u-text-error' : ''}>
                      {typeof stats.skewness === 'number' ? stats.skewness.toFixed(2) : stats.skewness}
                    </td>
                    <th>Test Normalità</th><td>{stats.normality_flag}</td>
                  </tr>
                  <tr>
                    <th>% Outliers (IQR)</th>
                    <td className={stats.outlier_iqr_pct > 5 ? 'u-text-error' : ''}>{stats.outlier_iqr_pct}%</td>
                    <th></th><td></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {col.suggestions?.length > 0 && (
            <div className="u-flex u-flex-col u-gap-2">
              {col.suggestions.map((s, i) => (
                <div key={i} className={`alert alert--${s.priorita === 'high' ? 'error' : 'info'}`}>
                  <strong>{s.motivo}</strong> — {s.trasformazione}
                </div>
              ))}
            </div>
          )}

          <div className="charts-stack">
            {charts.histogram && <div className="card"><PlotlyChart chart={charts.histogram} height={300} /></div>}
            {charts.boxplot   && <div className="card"><PlotlyChart chart={charts.boxplot}   height={280} /></div>}
            {charts.qqplot    && <div className="card"><PlotlyChart chart={charts.qqplot}    height={300} /></div>}
            {charts.ecdf      && <div className="card"><PlotlyChart chart={charts.ecdf}      height={280} /></div>}
          </div>
        </>
      )}

      {/* Discreto / Categorico */}
      {(st === 'numeric_discrete' || st === 'categorical_nominal' || st === 'categorical_ordinal') && (
        <>
          <div className="card">
            <div className="table-container">
              <table className="table">
                <tbody>
                  <tr>
                    <th>N (Osservazioni)</th><td>{stats.count?.toLocaleString('it-IT')}</td>
                    <th>Valori Unici</th><td>{stats.n_unique}</td>
                  </tr>
                  <tr>
                    <th>Moda</th><td>{stats.mode}</td>
                    <th>% Mancanti</th><td>{stats.missing_pct}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          {charts.bar && <div className="card"><PlotlyChart chart={charts.bar} height={320} /></div>}

          {st === 'categorical_ordinal' && charts.cumulative_relative && (
            <div className="card">
              <PlotlyChart chart={charts.cumulative_relative} height={320} />
            </div>
          )}

          {st === 'categorical_nominal' && (charts.pareto || charts.treemap) && (
            <div className="charts-grid charts-grid--two">
              {charts.pareto && <div className="card"><PlotlyChart chart={charts.pareto} height={340} /></div>}
              {charts.treemap && <div className="card"><PlotlyChart chart={charts.treemap} height={340} /></div>}
            </div>
          )}
        </>
      )}

      {/* Booleano */}
      {st === 'boolean' && (
        <>
          <div className="card">
            <div className="table-container">
              <table className="table">
                <tbody>
                  <tr>
                    <th>% True</th><td className="u-text-error">{col.stats?.true_pct}%</td>
                    <th>% False</th><td>{col.stats?.false_pct}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div className="charts-grid charts-grid--two">
            {charts.bar && <div className="card"><PlotlyChart chart={charts.bar} height={280} /></div>}
            {charts.donut && <div className="card"><PlotlyChart chart={charts.donut} height={280} /></div>}
          </div>
        </>
      )}

      {/* Datetime */}
      {st === 'datetime' && (
        <>
          <div className="card">
            <div className="table-container">
              <table className="table">
                <tbody>
                  <tr>
                    <th>Min Date</th><td>{String(stats.min_date || '').slice(0, 10)}</td>
                    <th>Range (gg)</th><td>{stats.range_days}</td>
                  </tr>
                  <tr>
                    <th>Max Date</th><td>{String(stats.max_date || '').slice(0, 10)}</td>
                    <th>Date Uniche</th><td>{stats.n_unique?.toLocaleString('it-IT')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div className="charts-grid">
            {charts.by_year  && <div className="card"><PlotlyChart chart={charts.by_year}  height={280} /></div>}
            {charts.by_month && <div className="card"><PlotlyChart chart={charts.by_month} height={280} /></div>}
          </div>
        </>
      )}

      {/* Text / ID / Geographic */}
      {(st === 'text' || st === 'id' || st === 'geographic') && (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <tbody>
                {Object.entries(stats).reduce((result, item, index, array) => {
                  if (index % 2 === 0) result.push(array.slice(index, index + 2));
                  return result;
                }, []).map((pair, idx) => (
                  <tr key={idx}>
                    <th>{pair[0][0]}</th><td>{String(pair[0][1])}</td>
                    <th>{pair[1] ? pair[1][0] : ''}</th><td>{pair[1] ? String(pair[1][1]) : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
