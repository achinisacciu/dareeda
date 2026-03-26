import { StatCard } from '../StatCard';

export function InferenceSection({ data }) {
  const tests = data?.tests || [];
  const s     = data?.summary || {};

  return (
    <div className="u-flex u-flex-col u-gap-6">

      <div className="u-flex u-gap-4 u-flex-wrap">
        <StatCard label="Test eseguiti"       value={s.n_tests} />
        <StatCard label="Significativi (FDR)" value={s.significant_after_fdr} accent={s.significant_after_fdr > 0} />
      </div>

      {data.ai_comment && (
        <div className="insight">
          <div className="insight__header">
            <span className="insight__icon">◎</span>
            Osservazione
          </div>
          <div className="insight__content">{data.ai_comment}</div>
        </div>
      )}

      {tests.length > 0 && (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Target</th>
                  <th>Test</th>
                  <th className="numeric">p-value</th>
                  <th>Effect size</th>
                  <th className="center">Sig. FDR</th>
                </tr>
              </thead>
              <tbody>
                {tests.map((t, i) => (
                  <tr key={i} className={t.significant_fdr ? 'selected' : ''}>
                    <td className="u-font-medium">{t.feature}</td>
                    <td>{t.target}</td>
                    <td>
                      <span className="badge badge--neutral u-text-xs">{t.test}</span>
                    </td>
                    <td className={`numeric${t.significant_fdr ? ' u-text-error u-font-semibold' : ''}`}>
                      {t.pvalue}
                    </td>
                    <td className="u-text-secondary">{t.effect_label || '—'}</td>
                    <td className="center">
                      {t.significant_fdr
                        ? <span className="badge badge--success">✓</span>
                        : <span className="u-text-muted">—</span>
                      }
                    </td>
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
