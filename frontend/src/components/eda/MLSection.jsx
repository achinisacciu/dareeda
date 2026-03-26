import { PlotlyChart } from '../PlotlyChart';
import { StatCard } from '../StatCard';

export function MLSection({ data }) {
  const fi = data?.feature_importance;
  const cl = data?.clustering;
  const an = data?.anomaly_detection;
  const hasVisibleBlocks = (
    (fi && !fi.skipped) ||
    (cl && !cl.skipped) ||
    (an && !an.skipped)
  );

  return (
    <div className="u-flex u-flex-col u-gap-6">

      {data?.error && (
        <div className="insight">
          <div className="insight__header">
            <span className="insight__icon">◎</span>
            ML supervisionato non configurato
          </div>
          <div className="insight__content">{data.error}</div>
        </div>
      )}

      {fi && !fi.skipped && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Feature Importance</h3>
              <p className="card__subtitle">Mutual Information</p>
            </div>
          </div>
          {fi.ai_comment && (
            <div className="insight u-mb-4">
              <div className="insight__header">
                <span className="insight__icon">◎</span>
                Osservazione
              </div>
              <div className="insight__content">{fi.ai_comment}</div>
            </div>
          )}
          {fi.charts?.bar && <PlotlyChart chart={fi.charts.bar} height={320} />}
        </div>
      )}

      {cl && !cl.skipped && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Clustering KMeans</h3>
            </div>
          </div>
          {cl.ai_comment && (
            <div className="insight u-mb-4">
              <div className="insight__header">
                <span className="insight__icon">◎</span>
                Osservazione
              </div>
              <div className="insight__content">{cl.ai_comment}</div>
            </div>
          )}
          <div className="u-flex u-gap-4 u-flex-wrap u-mb-4">
            <StatCard label="K ottimale" value={cl.best_k} accent />
            {cl.cluster_sizes && Object.entries(cl.cluster_sizes).map(([k, n]) => (
              <StatCard key={k} label={`Cluster ${k}`} value={n.toLocaleString('it-IT')} />
            ))}
          </div>
          <div className="charts-grid">
            {cl.charts?.elbow      && <PlotlyChart chart={cl.charts.elbow}      height={280} />}
            {cl.charts?.silhouette && <PlotlyChart chart={cl.charts.silhouette} height={280} />}
            {cl.charts?.scatter    && <PlotlyChart chart={cl.charts.scatter}    height={320} />}
          </div>
        </div>
      )}

      {an && !an.skipped && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Anomaly Detection</h3>
            </div>
          </div>
          {an.ai_comment && (
            <div className="insight u-mb-4">
              <div className="insight__header">
                <span className="insight__icon">◎</span>
                Osservazione
              </div>
              <div className="insight__content">{an.ai_comment}</div>
            </div>
          )}
          <div className="u-flex u-gap-4 u-flex-wrap u-mb-4">
            <StatCard label="Isolation Forest" value={`${an.isolation_forest?.n_anomalies} (${an.isolation_forest?.pct}%)`} accent />
            <StatCard label="LOF"              value={`${an.lof?.n_anomalies} (${an.lof?.pct}%)`} />
            <StatCard label="Consenso"         value={`${an.consensus?.n_anomalies} (${an.consensus?.pct}%)`} />
          </div>
          {an.charts?.score_distribution && (
            <PlotlyChart chart={an.charts.score_distribution} height={300} />
          )}
        </div>
      )}

      {!data?.error && !hasVisibleBlocks && (
        <div className="insight">
          <div className="insight__header">
            <span className="insight__icon">◎</span>
            Nessun risultato ML
          </div>
          <div className="insight__content">
            L&apos;analisi ML non ha prodotto output visualizzabili per questo dataset.
          </div>
        </div>
      )}

    </div>
  );
}
