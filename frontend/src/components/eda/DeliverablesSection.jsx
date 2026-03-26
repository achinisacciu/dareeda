import { StatCard } from '../StatCard';

export function DeliverablesSection({ data }) {
  if (!data) return null;

  const frontMatter = data.front_matter || {};
  const cover = frontMatter.cover || {};
  const deliverables = data.deliverables || {};
  const metadata = deliverables.report_metadata || frontMatter.report_metadata || {};

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="u-flex u-gap-4 u-flex-wrap">
        <StatCard label="Versione" value={cover.version} />
        <StatCard label="Classificazione" value={cover.classification} />
        <StatCard label="Runtime" value={cover.runtime} />
        <StatCard label="Quality Score" value={metadata.quality_score} accent={metadata.quality_score >= 80} />
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <tbody>
              <tr><th>Titolo</th><td>{cover.title}</td><th>Sottotitolo</th><td>{cover.subtitle}</td></tr>
              <tr><th>Generato</th><td>{cover.generated_at}</td><th>Dataset hash</th><td>{cover.dataset_hash}</td></tr>
              <tr><th>Analyst</th><td>{cover.analyst}</td><th>Reviewer</th><td>{cover.reviewer}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {(deliverables.outputs || []).length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Output Artefacts</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Formato</th>
                  <th>Path</th>
                  <th>Hash</th>
                </tr>
              </thead>
              <tbody>
                {deliverables.outputs.map(item => (
                  <tr key={item.name}>
                    <td className="u-font-medium">{item.name}</td>
                    <td>{item.format}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.path}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.hash || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(deliverables.validation_checklist || []).length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Validation Checklist</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Check</th>
                  <th>Stato</th>
                  <th>Dettaglio</th>
                </tr>
              </thead>
              <tbody>
                {deliverables.validation_checklist.map(item => (
                  <tr key={item.check}>
                    <td className="u-font-medium">{item.check}</td>
                    <td><span className={`badge ${item.status ? 'badge--success' : 'badge--warning'}`}>{String(item.status)}</span></td>
                    <td>{item.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(deliverables.approvals || []).length > 0 && (
        <div className="card">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Approvals</h3>
            </div>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Ruolo</th>
                  <th>Stato</th>
                </tr>
              </thead>
              <tbody>
                {deliverables.approvals.map(item => (
                  <tr key={item.role}>
                    <td className="u-font-medium">{item.role}</td>
                    <td><span className="badge badge--neutral">{item.status}</span></td>
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
