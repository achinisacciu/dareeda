import { StatCard } from '../StatCard';
import { PlotlyChart } from '../PlotlyChart';

const SEV_COLOR = { none: '#ccc', low: '#1B272F', moderate: '#59ADF7', high: '#E4002B', critical: '#B80023' };

export function DataQualitySection({ data }) {
  if (!data) return null;
  const m = data.missing || {};
  const d = data.duplicates || {};
  const g = m.global || {};

  return (
    <div className="u-flex u-flex-col u-gap-6">

      {/* Missing values - KPI */}
      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Missing values</h3>
          </div>
        </div>
        <div className="u-flex u-gap-4 u-flex-wrap">
          <StatCard label="Righe con missing"  value={`${g.pct_rows_with_missing ?? 0}%`} accent={g.pct_rows_with_missing > 20} />
          <StatCard label="Celle mancanti"     value={g.total_missing_cells?.toLocaleString('it-IT')} />
          <StatCard label="% celle mancanti"   value={`${g.pct_missing_cells ?? 0}%`} />
          <StatCard label="Media missing/riga" value={g.mean_missing_per_row} />
        </div>

        {m.ai_comment && (
          <div className="insight u-mt-4">
            <div className="insight__header">
              <span className="insight__icon">◎</span>
              Osservazione
            </div>
            <div className="insight__content">{m.ai_comment}</div>
          </div>
        )}
      </div>

      {/* Grafici missing */}
      {(m.charts?.missing_bar || m.charts?.missing_heatmap) && (
        <div className="u-flex u-flex-col u-gap-4">
          {m.charts?.missing_bar && (
            <div className="card">
              <PlotlyChart chart={m.charts.missing_bar} height={300} />
            </div>
          )}
          {m.charts?.missing_heatmap && (
            <div className="card">
              <PlotlyChart chart={m.charts.missing_heatmap} height={280} />
            </div>
          )}
        </div>
      )}

      {(m.charts?.missing_cooccurrence || m.charts?.missing_pattern_correlation || m.charts?.missing_dendrogram) && (
        <div className="u-flex u-flex-col u-gap-4">
          {m.charts?.missing_cooccurrence && (
            <div className="card">
              <PlotlyChart chart={m.charts.missing_cooccurrence} height={420} />
            </div>
          )}
          {m.charts?.missing_pattern_correlation && (
            <div className="card">
              <PlotlyChart chart={m.charts.missing_pattern_correlation} height={420} />
            </div>
          )}
          {m.charts?.missing_dendrogram && (
            <div className="card">
              <PlotlyChart chart={m.charts.missing_dendrogram} height={460} />
            </div>
          )}
        </div>
      )}

      {/* Tabella colonne per severità */}
      {m.per_column?.some(c => c.missing_count > 0) && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Colonne per severità missing</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Variabile</th>
                  <th className="numeric">Missing</th>
                  <th className="numeric">%</th>
                  <th>Severità</th>
                </tr>
              </thead>
              <tbody>
                {m.per_column
                  .filter(c => c.missing_count > 0)
                  .sort((a, b) => b.missing_pct - a.missing_pct)
                  .map(c => (
                    <tr key={c.variable}>
                      <td className="u-font-medium">{c.variable}</td>
                      <td className="numeric">{c.missing_count.toLocaleString('it-IT')}</td>
                      <td className="numeric">{c.missing_pct}%</td>
                      <td>
                        <span
                          className="badge"
                          style={{ color: SEV_COLOR[c.severity], background: `${SEV_COLOR[c.severity]}18`, border: `1px solid ${SEV_COLOR[c.severity]}33` }}
                        >
                          {c.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Duplicati */}
      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Duplicati</h3>
          </div>
        </div>
        <div className="u-flex u-gap-4 u-flex-wrap">
          <StatCard label="Righe duplicate" value={d.n_duplicate_rows?.toLocaleString('it-IT')} accent={d.pct_duplicate_rows > 5} />
          <StatCard label="% duplicate"     value={`${d.pct_duplicate_rows ?? 0}%`} />
          <StatCard label="Righe uniche"    value={d.n_unique_rows?.toLocaleString('it-IT')} />
        </div>

        {d.ai_comment && (
          <div className="insight u-mt-4">
            <div className="insight__header">
              <span className="insight__icon">◎</span>
              Osservazione
            </div>
            <div className="insight__content">{d.ai_comment}</div>
          </div>
        )}
      </div>

      {/* Candidati esclusione */}
      {data.inconsistencies?.candidates_exclusion?.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Candidati all&apos;esclusione</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Variabile</th>
                  <th>Motivo</th>
                  <th>Evidenza</th>
                </tr>
              </thead>
              <tbody>
                {data.inconsistencies.candidates_exclusion.map(c => (
                  <tr key={c.variable}>
                    <td className="u-font-medium">{c.variable}</td>
                    <td>
                      <span className="badge badge--error">{c.reason}</span>
                    </td>
                    <td className="u-text-secondary u-text-sm">{c.evidence}</td>
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
