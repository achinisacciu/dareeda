export function AdvancedAnalyticsSection({ data }) {
  if (!data) return null;

  return (
    <div className="u-flex u-flex-col u-gap-6">
      {(data.applicability || []).length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Applicability Matrix</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Analisi</th>
                  <th>Applicabile</th>
                  <th>Motivo</th>
                </tr>
              </thead>
              <tbody>
                {data.applicability.map(item => (
                  <tr key={item.analysis}>
                    <td className="u-font-medium">{item.analysis}</td>
                    <td><span className={`badge ${item.applicable ? 'badge--success' : 'badge--neutral'}`}>{String(item.applicable)}</span></td>
                    <td>{item.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.time_decomposition && (
        <div className="insight">
          <div className="insight__header">
            <span className="insight__icon">◬</span>
            Time Decomposition
          </div>
          <div className="insight__content">
            Serie: {data.time_decomposition.series}. Stato: {data.time_decomposition.stationarity}. {data.time_decomposition.note}
          </div>
        </div>
      )}
    </div>
  );
}
