import { StatCard } from '../StatCard';

export function ExecutiveSection({ data }) {
  if (!data) return null;

  const business = data.business_context || {};
  const keyMetrics = data.key_metrics || [];
  const alerts = data.critical_alerts || [];
  const actions = data.action_items || [];
  const recommendation = data.recommendation || {};
  const quality = data.quality_score_decomposition || {};

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="u-flex u-gap-4 u-flex-wrap">
        <StatCard label="Quality Score" value={quality.total_score} accent={quality.total_score >= 80} />
        <StatCard label="Band" value={quality.quality_band} />
        <StatCard label="Recommendation" value={recommendation.label} accent={recommendation.ready_for_modeling} />
      </div>

      {data.executive_summary && (
        <div className="insight">
          <div className="insight__header">
            <span className="insight__icon">◆</span>
            Executive Summary
          </div>
          <div className="insight__content">{data.executive_summary}</div>
        </div>
      )}

      <div className="card">
        <div className="table-container">
          <table className="table">
            <tbody>
              <tr><th>Progetto</th><td>{business.project}</td><th>Obiettivo</th><td>{business.objective}</td></tr>
              <tr><th>Stakeholder</th><td>{business.stakeholder}</td><th>Timeline</th><td>{business.timeline}</td></tr>
              <tr><th>Impatto atteso</th><td colSpan={3}>{business.expected_impact}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {keyMetrics.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Key Metrics</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Metrica</th>
                  <th className="numeric">Valore</th>
                  <th>Benchmark</th>
                  <th>Stato</th>
                </tr>
              </thead>
              <tbody>
                {keyMetrics.map(metric => (
                  <tr key={metric.metric}>
                    <td className="u-font-medium">{metric.metric}</td>
                    <td className="numeric">{metric.value}</td>
                    <td>{metric.benchmark}</td>
                    <td><span className="badge badge--neutral">{metric.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {alerts.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Critical Alerts</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Issue</th>
                  <th>Colonne</th>
                  <th>Azione</th>
                  <th>Owner</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, idx) => (
                  <tr key={`${alert.issue}-${idx}`}>
                    <td><span className="badge badge--error">{alert.severity}</span></td>
                    <td className="u-font-medium">{alert.issue}</td>
                    <td>{alert.columns}</td>
                    <td>{alert.immediate_action}</td>
                    <td>{alert.owner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {actions.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Action Items</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th className="numeric">Priority</th>
                  <th>Titolo</th>
                  <th>Owner</th>
                  <th>Deadline</th>
                  <th>Azione</th>
                </tr>
              </thead>
              <tbody>
                {actions.map(action => (
                  <tr key={`${action.priority}-${action.title}`}>
                    <td className="numeric">{action.priority}</td>
                    <td className="u-font-medium">{action.title}</td>
                    <td>{action.owner}</td>
                    <td>{action.deadline}</td>
                    <td>{action.action}</td>
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
