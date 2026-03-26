import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { StatCard } from '../StatCard';
import { analysisApi } from '../../api/client';
import { Spinner } from '../Spinner';

const SEV_COLOR = {
  low: '#1B272F',
  medium: '#59ADF7',
  high: '#E4002B',
};

const SUPPORT_LABEL = {
  true: 'Azione disponibile',
  false: 'Solo revisione',
};

function formatCount(value) {
  if (value === null || value === undefined) return '0';
  if (typeof value === 'number') return value.toLocaleString('it-IT');
  return String(value);
}

function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0%';
  return `${Number(value).toLocaleString('it-IT')}%`;
}

function describeAction(action) {
  const type = action?.type;
  const column = action?.column;

  if (type === 'exclude_column') return `Esclusione colonna${column ? `: ${column}` : ''}`;
  if (type === 'drop_duplicate_rows') return 'Deduplicazione righe esatte';
  if (type === 'replace_values') return `Conversione token in null${column ? `: ${column}` : ''}`;
  if (type === 'trim_whitespace') return `Trim spazi${column ? `: ${column}` : ''}`;
  return type || 'Azione';
}

function toCleaningAction(issue) {
  const action = issue?.action || {};
  if (!action?.type) return null;
  return {
    type: action.type,
    column: action.column ?? issue?.column ?? null,
    params: action.params || {},
  };
}

function buildDetectionRows(dq) {
  const missingCells = dq?.missing?.global?.total_missing_cells || 0;
  const duplicateRows = dq?.duplicates?.n_duplicate_rows || 0;
  const candidateColumns = dq?.inconsistencies?.candidates_exclusion?.length || 0;
  const maskedMissing = (dq?.text_cleaning?.masked_missing || []).reduce((sum, item) => sum + (item?.count || 0), 0);
  const whitespaceCells = (dq?.text_cleaning?.whitespace || []).reduce((sum, item) => sum + (item?.count || 0), 0);

  return [
    {
      label: 'Missing già riconosciuti',
      value: formatCount(missingCells),
      detail: 'Celle già nulle nel dataset. Nessuna regex.',
    },
    {
      label: 'Righe duplicate esatte',
      value: formatCount(duplicateRows),
      detail: 'Confronto esatto su tutte le colonne.',
    },
    {
      label: 'Colonne candidate esclusione',
      value: formatCount(candidateColumns),
      detail: 'Colonne costanti, quasi costanti o con missing eccessivo.',
    },
    {
      label: 'Token testuali da convertire in null',
      value: formatCount(maskedMissing),
      detail: 'Match esatto con trim + lowercase. Nessuna regex.',
    },
    {
      label: 'Celle con spazi da normalizzare',
      value: formatCount(whitespaceCells),
      detail: 'Rimozione dei soli spazi iniziali/finali.',
    },
  ];
}

function buildEvidence(issue) {
  const evidence = issue?.evidence || {};
  const rows = [];

  if (issue?.column) rows.push({ label: 'Colonna', value: issue.column });
  if (evidence.n_duplicate_rows !== undefined) rows.push({ label: 'Righe duplicate', value: formatCount(evidence.n_duplicate_rows) });
  if (evidence.pct_duplicate_rows !== undefined) rows.push({ label: '% duplicate', value: formatPct(evidence.pct_duplicate_rows) });
  if (evidence.affected_count !== undefined) rows.push({ label: 'Celle coinvolte', value: formatCount(evidence.affected_count) });
  if (evidence.affected_pct !== undefined) rows.push({ label: '% colpita', value: formatPct(evidence.affected_pct) });
  if (evidence.reason) rows.push({ label: 'Motivo', value: evidence.reason });
  if (evidence.evidence) rows.push({ label: 'Evidenza', value: evidence.evidence });
  if (evidence.unique_count !== undefined && evidence.unique_count !== null) rows.push({ label: 'Valori unici', value: formatCount(evidence.unique_count) });
  if (evidence.dominant_share !== undefined && evidence.dominant_share !== null) rows.push({ label: 'Valore dominante', value: formatPct(evidence.dominant_share) });
  if (Array.isArray(evidence.tokens) && evidence.tokens.length > 0) rows.push({ label: 'Token', value: evidence.tokens.map(token => token === '' ? '(stringa vuota)' : token).join(', ') });

  return rows;
}

export function CleaningSection({ data }) {
  const dq = data?.data_quality || data || {};
  const issues = dq?.standardized_issues || [];
  const cleaningSummary = dq?.cleaning_summary || {};
  const appliedCleaning = data?.applied_cleaning || {};
  const detectionRows = useMemo(() => buildDetectionRows(dq), [dq]);

  const actionableIssues = useMemo(
    () => issues.filter(issue => (issue?.proposal || {}).supported),
    [issues],
  );
  const reviewOnlyIssues = useMemo(
    () => issues.filter(issue => !(issue?.proposal || {}).supported),
    [issues],
  );

  const [selected, setSelected] = useState(() => new Set());
  const [rerunLoading, setRerunLoading] = useState(false);
  const [rerunError, setRerunError] = useState(null);

  const selectedIssues = useMemo(
    () => actionableIssues.filter(issue => selected.has(issue.id)),
    [actionableIssues, selected],
  );

  const selectedColumns = useMemo(
    () => new Set(selectedIssues.filter(issue => issue?.action?.type === 'exclude_column' && issue?.column).map(issue => issue.column)),
    [selectedIssues],
  );

  const estimatedResult = useMemo(() => {
    const rowsBefore = data?.n_rows_full ?? cleaningSummary?.dataset_shape?.rows ?? 0;
    const colsBefore = data?.n_cols ?? cleaningSummary?.dataset_shape?.columns ?? 0;
    let rowsAfter = rowsBefore;
    let cellsModified = 0;

    selectedIssues.forEach(issue => {
      const impact = issue?.proposal?.impact || {};
      if (typeof impact.rows_after === 'number') {
        rowsAfter = Math.min(rowsAfter, impact.rows_after);
      }
      cellsModified += impact.cells_modified || 0;
    });

    return {
      rowsBefore,
      rowsAfter,
      colsBefore,
      colsAfter: Math.max(colsBefore - selectedColumns.size, 0),
      cellsModified,
    };
  }, [data?.n_cols, data?.n_rows_full, cleaningSummary?.dataset_shape?.columns, cleaningSummary?.dataset_shape?.rows, selectedColumns, selectedIssues]);

  const counts = useMemo(() => {
    const base = { low: 0, medium: 0, high: 0 };
    issues.forEach(issue => {
      const sev = issue?.severity || 'medium';
      if (sev in base) base[sev] += 1;
    });
    return base;
  }, [issues]);

  const nav = useNavigate();

  const datasetId = data?.dataset_id || null;
  const target = data?.target || null;
  const problemType = data?.problem_type || null;

  const toggle = (issueId) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(issueId)) next.delete(issueId);
      else next.add(issueId);
      return next;
    });
  };

  const selectAll = () => {
    setSelected(new Set(actionableIssues.map(issue => issue.id)));
  };

  const clearSelection = () => {
    setSelected(new Set());
  };

  const runSelectedCleaning = async () => {
    if (!datasetId || !selectedIssues.length) return;

    setRerunLoading(true);
    setRerunError(null);

    try {
      const cleaning_actions = selectedIssues
        .map(toCleaningAction)
        .filter(Boolean);

      const { data: resp } = await analysisApi.run(datasetId, {
        target: target || null,
        problem_type: problemType || null,
        cleaning_actions,
      });
      nav(`/analysis/${resp.analysis_id}`);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || 'Errore';
      setRerunError(String(msg));
    } finally {
      setRerunLoading(false);
    }
  };

  const hasAppliedCleaning = (appliedCleaning?.actions || []).length > 0;

  if (!issues.length && !hasAppliedCleaning) {
    return (
      <div className="insight">
        <div className="insight__header">Nessuna proposta di pulizia</div>
        <div className="insight__content">Per questo dataset non risultano trasformazioni o revisioni suggerite.</div>
      </div>
    );
  }

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="card card--flat">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Come leggere questa sezione</h3>
            <p className="card__subtitle">Ogni proposta separa chiaramente rilevazione, metodo tecnico e risultato atteso prima di lanciare una nuova analisi.</p>
          </div>
        </div>

        <div className="cleaning-guide">
          <div className="cleaning-guide__item">
            <div className="cleaning-guide__label">1. Rilevato</div>
            <div className="cleaning-guide__text">Ti diciamo cosa è stato trovato, su quale colonna e con quale logica di detection.</div>
          </div>
          <div className="cleaning-guide__item">
            <div className="cleaning-guide__label">2. Proposta</div>
            <div className="cleaning-guide__text">Specifichiamo se stiamo escludendo una colonna, rimuovendo duplicati, convertendo token in `null` o facendo trim degli spazi.</div>
          </div>
          <div className="cleaning-guide__item">
            <div className="cleaning-guide__label">3. Risultato</div>
            <div className="cleaning-guide__text">Mostriamo l&apos;effetto stimato sul dataset prima che tu decida di applicare l&apos;azione.</div>
          </div>
        </div>
      </div>

      {hasAppliedCleaning && (
        <div className="card card--info">
          <div className="card__header">
            <div className="card__header-left">
              <h3 className="card__title">Pulizia già applicata a questa analisi</h3>
              <p className="card__subtitle">
                La vista corrente deriva da un dataset già ripulito: righe {formatCount(appliedCleaning?.before_rows)} {'->'} {formatCount(appliedCleaning?.after_rows)},
                colonne {formatCount(appliedCleaning?.before_cols)} {'->'} {formatCount(appliedCleaning?.after_cols)}.
              </p>
            </div>
          </div>

          <div className="cleaning-chip-row">
            {(appliedCleaning?.actions || []).map((action, idx) => (
              <span key={`${action?.type || 'action'}-${idx}`} className="cleaning-chip">
                {describeAction(action)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Riepilogo pulizia</h3>
            <p className="card__subtitle">Panoramica di gravità, proposte azionabili e stima del dataset se applichi la selezione corrente.</p>
          </div>
        </div>

        <div className="u-flex u-gap-4 u-flex-wrap">
          <StatCard label="Issue totali" value={issues.length} />
          <StatCard label="Azionabili" value={actionableIssues.length} accent={actionableIssues.length > 0} />
          <StatCard label="Solo revisione" value={reviewOnlyIssues.length} />
          <StatCard label="High" value={counts.high} accent={counts.high > 0} />
          <StatCard label="Selezionate" value={selectedIssues.length} accent={selectedIssues.length > 0} />
        </div>

        <div className="cleaning-estimate">
          <div className="cleaning-estimate__item">
            <span className="cleaning-estimate__label">Righe stimate</span>
            <strong>{formatCount(estimatedResult.rowsBefore)} {'->'} {formatCount(estimatedResult.rowsAfter)}</strong>
          </div>
          <div className="cleaning-estimate__item">
            <span className="cleaning-estimate__label">Colonne stimate</span>
            <strong>{formatCount(estimatedResult.colsBefore)} {'->'} {formatCount(estimatedResult.colsAfter)}</strong>
          </div>
          <div className="cleaning-estimate__item">
            <span className="cleaning-estimate__label">Celle modificate</span>
            <strong>{formatCount(estimatedResult.cellsModified)}</strong>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Cosa è stato rilevato</h3>
            <p className="card__subtitle">Inventario sintetico delle anomalie o opportunità di pulizia rilevate sul dataset.</p>
          </div>
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Rilevazione</th>
                <th className="numeric">Quantità</th>
                <th>Come viene interpretata</th>
              </tr>
            </thead>
            <tbody>
              {detectionRows.map(row => (
                <tr key={row.label}>
                  <td className="u-font-medium">{row.label}</td>
                  <td className="numeric">{row.value}</td>
                  <td className="u-text-secondary u-text-sm">{row.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card card--flat">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Piano di pulizia</h3>
            <p className="card__subtitle">Seleziona solo le trasformazioni che vuoi davvero applicare. Nessuna modifica parte automaticamente.</p>
          </div>
          <div className="card__header-right">
            <button className="btn btn--ghost" type="button" onClick={selectAll} disabled={!actionableIssues.length || rerunLoading}>
              Seleziona tutto
            </button>
            <button className="btn btn--ghost" type="button" onClick={clearSelection} disabled={!selectedIssues.length || rerunLoading}>
              Pulisci selezione
            </button>
            <button
              className="btn btn--primary"
              disabled={rerunLoading || selectedIssues.length === 0 || !datasetId}
              onClick={runSelectedCleaning}
            >
              {rerunLoading ? (
                <>
                  <Spinner size={16} />
                  <span>Rieseguo...</span>
                </>
              ) : (
                <span>Applica e riesegui analisi</span>
              )}
            </button>
          </div>
        </div>

        {rerunError && (
          <div className="alert alert--error">
            <span>⚠</span>
            <span>{rerunError}</span>
          </div>
        )}
      </div>

      <div className="u-flex u-flex-col u-gap-4">
        {issues.map(issue => {
          const sev = issue?.severity || 'medium';
          const badgeColor = SEV_COLOR[sev] || SEV_COLOR.medium;
          const supported = !!issue?.proposal?.supported;
          const isSelected = selected.has(issue.id);
          const evidenceRows = buildEvidence(issue);
          const examples = issue?.preview?.examples || [];

          return (
            <div key={issue?.id || `${issue?.module}-${issue?.issue}-${issue?.column || 'dataset'}`} className="card cleaning-issue">
              <div className="card__header">
                <div className="card__header-left">
                  <h3 className="card__title">{issue?.title || issue?.issue || 'Issue'}</h3>
                  <p className="card__subtitle">
                    {(issue?.scope || {}).label || 'Intero dataset'} • {issue?.proposal?.action_label || describeAction(issue?.action)}
                  </p>
                </div>

                <div className="card__header-right">
                  <span
                    className="badge"
                    style={{
                      color: badgeColor,
                      background: `${badgeColor}18`,
                      border: `1px solid ${badgeColor}33`,
                    }}
                  >
                    {sev}
                  </span>
                  <span className={`badge ${supported ? 'badge--success' : 'badge--warning'}`}>
                    {SUPPORT_LABEL[String(supported)]}
                  </span>
                </div>
              </div>

              <div className="cleaning-issue__grid">
                <div className="cleaning-block">
                  <div className="cleaning-block__label">Rilevato</div>
                  <p className="cleaning-block__text">{issue?.detection?.summary}</p>
                  <p className="cleaning-block__meta">{issue?.detection?.details}</p>
                </div>

                <div className="cleaning-block">
                  <div className="cleaning-block__label">Metodo</div>
                  <p className="cleaning-block__text">{issue?.proposal?.method?.label || issue?.detection?.method?.label || describeAction(issue?.action)}</p>
                  <div className="cleaning-chip-row">
                    <span className="cleaning-chip">Regex: {(issue?.proposal?.method?.uses_regex || issue?.detection?.method?.uses_regex) ? 'sì' : 'no'}</span>
                    <span className="cleaning-chip">Tecnica: {issue?.action?.type || 'review_only'}</span>
                  </div>
                  {(issue?.proposal?.method?.notes || issue?.detection?.method?.notes) && (
                    <p className="cleaning-block__meta">{issue?.proposal?.method?.notes || issue?.detection?.method?.notes}</p>
                  )}
                </div>

                <div className="cleaning-block">
                  <div className="cleaning-block__label">Se applichi</div>
                  <p className="cleaning-block__text">{issue?.proposal?.result}</p>
                  <p className="cleaning-block__meta">{issue?.proposal?.summary}</p>
                </div>
              </div>

              {evidenceRows.length > 0 && (
                <div className="cleaning-evidence">
                  {evidenceRows.map(row => (
                    <div key={`${issue?.id}-${row.label}`} className="cleaning-evidence__item">
                      <span className="cleaning-evidence__label">{row.label}</span>
                      <strong className="cleaning-evidence__value">{row.value}</strong>
                    </div>
                  ))}
                </div>
              )}

              {examples.length > 0 && (
                <div className="table-container u-mt-4">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Prima</th>
                        <th>Dopo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {examples.map((example, idx) => (
                        <tr key={`${issue?.id}-example-${idx}`}>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{String(example?.before)}</td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{example?.after === null ? 'null' : String(example?.after)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="cleaning-issue__footer">
                {supported ? (
                  <label className="cleaning-checkbox">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggle(issue.id)}
                    />
                    <span>{isSelected ? 'Azione selezionata per la prossima analisi' : 'Seleziona questa azione'}</span>
                  </label>
                ) : (
                  <div className="u-text-secondary u-text-sm">Segnalazione informativa: nessuna trasformazione automatica disponibile.</div>
                )}

                <span className="u-text-muted u-text-sm" style={{ fontFamily: 'var(--font-mono)' }}>
                  {describeAction(issue?.action)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
