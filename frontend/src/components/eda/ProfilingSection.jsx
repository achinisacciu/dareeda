import { StatCard } from '../StatCard';
import { PlotlyChart } from '../PlotlyChart';

export function ProfilingSection({ data }) {
  if (!data) return null;

  const lineage = data.lineage || {};
  const structure = data.structural_overview || {};
  const semanticSummary = data.semantic_summary || [];
  const schema = data.master_schema || [];
  const pii = data.pii_candidates || [];

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="u-flex u-gap-4 u-flex-wrap">
        <StatCard label="Rows" value={structure.n_rows?.toLocaleString('it-IT')} />
        <StatCard label="Columns" value={structure.n_columns} />
        <StatCard label="Cells" value={structure.n_cells?.toLocaleString('it-IT')} />
        <StatCard label="Memory" value={structure.memory_mb} unit="MB" />
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <tbody>
              <tr><th>Sorgente primaria</th><td>{lineage.primary_source}</td><th>System of record</th><td>{lineage.system_of_record}</td></tr>
              <tr><th>Estrazione</th><td>{lineage.extraction_mode}</td><th>Frequenza update</th><td>{lineage.update_frequency}</td></tr>
              <tr><th>Last refresh</th><td>{lineage.last_refresh}</td><th>Owner</th><td>{lineage.source_owner}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {(data.charts?.semantic_treemap || data.charts?.cardinality_missing_scatter) && (
        <div className="charts-grid charts-grid--two">
          {data.charts?.semantic_treemap && <div className="card"><PlotlyChart chart={data.charts.semantic_treemap} height={340} /></div>}
          {data.charts?.cardinality_missing_scatter && <div className="card"><PlotlyChart chart={data.charts.cardinality_missing_scatter} height={340} /></div>}
        </div>
      )}

      {semanticSummary.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Semantic Summary</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Categoria</th>
                  <th className="numeric">Count</th>
                  <th className="numeric">%</th>
                  <th>Esempi</th>
                </tr>
              </thead>
              <tbody>
                {semanticSummary.map(item => (
                  <tr key={item.category}>
                    <td className="u-font-medium">{item.category}</td>
                    <td className="numeric">{item.count}</td>
                    <td className="numeric">{item.pct}</td>
                    <td>{item.examples}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {pii.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">PII Candidate</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Colonna</th>
                  <th>Tipo</th>
                  <th className="numeric">Confidenza</th>
                  <th>Azione</th>
                </tr>
              </thead>
              <tbody>
                {pii.map(item => (
                  <tr key={item.column}>
                    <td className="u-font-medium">{item.column}</td>
                    <td>{item.pii_type}</td>
                    <td className="numeric">{item.confidence}</td>
                    <td>{item.recommended_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {schema.length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Master Schema</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Colonna</th>
                  <th>Semantic type</th>
                  <th>Role</th>
                  <th className="numeric">Unique %</th>
                  <th className="numeric">Missing %</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {schema.map(col => (
                  <tr key={col.column}>
                    <td className="numeric">{col.index}</td>
                    <td className="u-font-medium">{col.column}</td>
                    <td>{col.semantic_type}</td>
                    <td>{col.role}</td>
                    <td className="numeric">{col.uniqueness_ratio}</td>
                    <td className="numeric">{col.pct_missing}</td>
                    <td><span className="badge badge--neutral">{col.status}</span></td>
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
