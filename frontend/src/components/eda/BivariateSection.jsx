import { useState } from 'react';
import { PlotlyChart } from '../PlotlyChart';

const SUB_TABS = [
  { key: 'num_num', label: 'Num x Num' },
  { key: 'num_cat', label: 'Num x Cat' },
  { key: 'cat_cat', label: 'Cat x Cat' },
];

export function BivariateSection({ data }) {
  const available = SUB_TABS.filter(t => data?.[t.key] && !data[t.key].skipped);
  const [active, setActive] = useState(available[0]?.key || null);

  if (available.length === 0) return (
    <div className="insight">
      <div className="insight__header">Nessuna analisi bivariata disponibile.</div>
    </div>
  );

  const nn = data.num_num;
  const nc = data.num_cat;
  const cc = data.cat_cat;

  return (
    <div className="u-flex u-flex-col u-gap-4">

      <div className="tabs__nav" role="tablist">
        {available.map(t => (
          <button
            key={t.key}
            role="tab"
            aria-selected={active === t.key}
            className={`tab${active === t.key ? ' tab--active' : ''}`}
            onClick={() => setActive(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {active === 'num_num' && nn && (
        <div className="u-flex u-flex-col u-gap-4">
          {nn.ai_comment && (
            <div className="insight">
              <div className="insight__header">
                <span className="insight__icon">◎</span>
                Osservazione
              </div>
              <div className="insight__content">{nn.ai_comment}</div>
            </div>
          )}
          {nn.charts?.correlation_heatmap && (
            <div className="card">
              <PlotlyChart chart={nn.charts.correlation_heatmap} height={420} />
            </div>
          )}
          {nn.charts?.scatters && (
            <div className="charts-grid">
              {Object.entries(nn.charts.scatters).slice(0, 3).map(([k, chart]) => (
                <div key={k} className="card">
                  <PlotlyChart chart={chart} height={320} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {active === 'num_cat' && nc && (
        <div className="u-flex u-flex-col u-gap-4">
          {nc.ai_comment && (
            <div className="insight">
              <div className="insight__header">
                <span className="insight__icon">◎</span>
                Osservazione
              </div>
              <div className="insight__content">{nc.ai_comment}</div>
            </div>
          )}
          <div className="charts-grid">
            {nc.charts && Object.entries(nc.charts).map(([k, chart]) => (
              <div key={k} className="card">
                <PlotlyChart chart={chart} height={320} />
              </div>
            ))}
          </div>
        </div>
      )}

      {active === 'cat_cat' && cc && cc.pairs?.length > 0 && (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Var A</th>
                  <th>Var B</th>
                  <th className="numeric">Cramer&apos;s V</th>
                  <th className="numeric">p-value (chi2)</th>
                </tr>
              </thead>
              <tbody>
                {cc.pairs.map((p, i) => (
                  <tr key={i}>
                    <td className="u-font-medium">{p.var_a}</td>
                    <td className="u-font-medium">{p.var_b}</td>
                    <td className={`numeric${p.cramers_v > 0.3 ? ' u-text-error' : ''}`}>
                      {p.cramers_v}
                    </td>
                    <td className="numeric">{p.chi2_pvalue}</td>
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
