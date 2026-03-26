import { PlotlyChart } from '../PlotlyChart';
import { StatCard } from '../StatCard';

export function TimeSeriesSection({ data }) {
  if (!data?.active) return (
    <div className="insight">
      <div className="insight__header">
        <span className="insight__icon">◷</span>
        Non applicabile
      </div>
      <div className="insight__content">
        Nessuna colonna datetime rilevata — analisi non applicabile.
      </div>
    </div>
  );

  return (
    <div className="u-flex u-flex-col u-gap-6">

      <div className="insight">
        <div className="insight__header">
          <span className="insight__icon">◷</span>
          Colonna temporale
        </div>
        <div className="insight__content">
          <strong>{data.ts_column}</strong>
        </div>
      </div>

      {Object.entries(data.analyses || {}).map(([col, analysis]) => (
        <div key={col} className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">{col}</h3>
            </div>
          </div>

          {analysis.error ? (
            <div className="alert alert--error">
              <span>⚠</span>
              <span>{analysis.error}</span>
            </div>
          ) : (
            <div className="u-flex u-flex-col u-gap-4">
              <div className="u-flex u-gap-4 u-flex-wrap">
                <StatCard label="N osservazioni" value={analysis.metadata?.n_observations?.toLocaleString('it-IT')} />
                <StatCard label="Da"  value={String(analysis.metadata?.min_date || '').slice(0, 10)} />
                <StatCard label="A"   value={String(analysis.metadata?.max_date || '').slice(0, 10)} />
                <StatCard label="ADF" value={analysis.stationarity?.decision} accent={analysis.stationarity?.decision === 'non stazionaria'} />
              </div>

              {analysis.ai_comment && (
                <div className="insight">
                  <div className="insight__header">
                    <span className="insight__icon">◎</span>
                    Osservazione
                  </div>
                  <div className="insight__content">{analysis.ai_comment}</div>
                </div>
              )}

              <div className="charts-grid">
                {analysis.charts?.line && <PlotlyChart chart={analysis.charts.line} height={300} />}
                {analysis.charts?.acf  && <PlotlyChart chart={analysis.charts.acf}  height={260} />}
              </div>
            </div>
          )}
        </div>
      ))}

    </div>
  );
}
