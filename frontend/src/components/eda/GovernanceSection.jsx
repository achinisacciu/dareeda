export function GovernanceSection({ data }) {
  if (!data) return null;

  const pii = data.pii_detection || [];
  const fairness = data.fairness || {};

  return (
    <div className="u-flex u-flex-col u-gap-6">
      {pii.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">PII Detection</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Colonna</th>
                  <th>Tipo</th>
                  <th className="numeric">Confidenza</th>
                  <th>Motivo</th>
                  <th>Azione</th>
                </tr>
              </thead>
              <tbody>
                {pii.map(item => (
                  <tr key={item.column}>
                    <td className="u-font-medium">{item.column}</td>
                    <td>{item.pii_type}</td>
                    <td className="numeric">{item.confidence}</td>
                    <td>{item.reason}</td>
                    <td>{item.recommended_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Fairness</h3>
          </div>
        </div>
        {fairness.applicable ? (
          <div className="u-flex u-flex-col u-gap-4">
            <div className="insight">
              <div className="insight__header">
                <span className="insight__icon">⚖</span>
                Outcome monitorato
              </div>
              <div className="insight__content">Classe positiva monitorata: {fairness.positive_class}</div>
            </div>
            {(fairness.group_metrics || []).length > 0 ? (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Attributo</th>
                      <th>Tipo</th>
                      <th className="numeric">Disparate impact</th>
                      <th>Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fairness.group_metrics.map(metric => (
                      <tr key={metric.attribute}>
                        <td className="u-font-medium">{metric.attribute}</td>
                        <td>{metric.attribute_type}</td>
                        <td className="numeric">{metric.disparate_impact_ratio}</td>
                        <td><span className="badge badge--neutral">{metric.severity}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="insight">
                <div className="insight__content">Nessun attributo protetto con massa critica sufficiente per metriche affidabili.</div>
              </div>
            )}
          </div>
        ) : (
          <div className="insight">
            <div className="insight__content">{fairness.reason}</div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Methodology</h3>
          </div>
        </div>
        <div className="u-flex u-flex-col u-gap-2">
          {(data.methodology || []).map(item => (
            <div key={item} className="insight">
              <div className="insight__content">{item}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Limitazioni</h3>
          </div>
        </div>
        <div className="u-flex u-flex-col u-gap-2">
          {(data.limitations || []).map(item => (
            <div key={item} className="alert alert--info">{item}</div>
          ))}
        </div>
        <div className="insight u-mt-4">
          <div className="insight__header">
            <span className="insight__icon">⚖</span>
            Disclaimer
          </div>
          <div className="insight__content">{data.disclaimer}</div>
        </div>
      </div>
    </div>
  );
}
