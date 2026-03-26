import { StatCard } from '../StatCard';

function countItems(items) {
  return Array.isArray(items) ? items.length : 0;
}

export function PredictivePrepSection({ data }) {
  if (!data) return null;

  const imbalance = data.class_imbalance || null;

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="u-flex u-gap-4 u-flex-wrap">
        <StatCard label="Feature Eng." value={countItems(data.feature_engineering)} />
        <StatCard label="Encoding rules" value={countItems(data.encoding_strategy)} />
        <StatCard label="Imputation rules" value={countItems(data.imputation_strategy)} />
        <StatCard label="Leakage risks" value={countItems(data.leakage_risk_assessment)} accent={countItems(data.leakage_risk_assessment) > 0} />
      </div>

      <div className="insight">
        <div className="insight__header">
          <span className="insight__icon">⬢</span>
          Pipeline suggerita
        </div>
        <div className="insight__content">
          {(data.preprocessing_pipeline || []).join(' -> ')}
        </div>
      </div>

      {imbalance && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Class Imbalance</h3>
            </div>
          </div>
          <div className="u-flex u-gap-4 u-flex-wrap u-mb-4">
            <StatCard label="Target" value={imbalance.target} />
            <StatCard label="Imbalance ratio" value={imbalance.imbalance_ratio || 'n/a'} accent={imbalance.severity !== 'ok'} />
            <StatCard label="Severity" value={imbalance.severity} accent={imbalance.severity !== 'ok'} />
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Classe</th>
                  <th className="numeric">Count</th>
                  <th className="numeric">%</th>
                </tr>
              </thead>
              <tbody>
                {(imbalance.distribution || []).map(row => (
                  <tr key={row.class}>
                    <td className="u-font-medium">{row.class}</td>
                    <td className="numeric">{row.count}</td>
                    <td className="numeric">{row.pct}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {[
        ['Feature Engineering', data.feature_engineering, [['Feature', 'feature'], ['Source', 'source_columns'], ['Formula', 'formula'], ['Status', 'status']]],
        ['Encoding Strategy', data.encoding_strategy, [['Colonna', 'column'], ['Strategia', 'strategy'], ['Missing %', 'missing_pct']]],
        ['Scaling Strategy', data.scaling_strategy, [['Colonna', 'column'], ['Strategia', 'strategy'], ['Outlier %', 'outlier_pct']]],
        ['Imputation Strategy', data.imputation_strategy, [['Colonna', 'column'], ['Missing %', 'missing_pct'], ['Severity', 'severity'], ['Strategia', 'strategy']]],
        ['Leakage Risks', data.leakage_risk_assessment, [['Colonna', 'column'], ['Rischio', 'risk'], ['Severity', 'severity'], ['Azione', 'recommended_action']]],
      ].map(([title, rows, cols]) => (
        rows?.length > 0 && (
          <div key={title} className="card">
            <div className="card__header">
              <div className="card__header-left">
                <h3 className="card__title">{title}</h3>
              </div>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    {cols.map(([label]) => <th key={label}>{label}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, idx) => (
                    <tr key={`${title}-${idx}`}>
                      {cols.map(([, key]) => <td key={key}>{String(row[key] ?? '—')}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      ))}

      <div className="card">
        <div className="table-container">
          <table className="table">
            <tbody>
              <tr><th>Split raccomandato</th><td>{data.split_strategy?.recommended}</td><th>Train</th><td>{data.split_strategy?.train}%</td></tr>
              <tr><th>Validation</th><td>{data.split_strategy?.validation}%</td><th>Test</th><td>{data.split_strategy?.test}%</td></tr>
              <tr><th>Note</th><td colSpan={3}>{data.split_strategy?.notes}</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
