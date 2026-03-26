import { useEffect, useMemo, useState } from 'react';
import { StatCard } from '../StatCard';
import { PlotlyChart } from '../PlotlyChart';
import { Spinner } from '../Spinner';
import { analysisApi } from '../../api/client';

const COLUMN_GROUPS = [
  { key: 'all', label: 'Tutte' },
  { key: 'numeric', label: 'Numeriche' },
  { key: 'categorical', label: 'Categoriche' },
  { key: 'datetime', label: 'Temporali' },
  { key: 'text', label: 'Testo' },
];

function formatTechnicalType(dtypeOriginal, semanticType) {
  const dt = String(dtypeOriginal || '').toLowerCase();
  if (semanticType === 'id') return 'ID / quasi-ID';
  if (semanticType === 'datetime') return 'Datetime';
  if (semanticType === 'boolean') return 'Booleano';

  if (semanticType === 'categorical_nominal' || semanticType === 'categorical_ordinal') return 'Categorico';
  if (semanticType === 'text') return 'Testo';

  if (dt.includes('int') || dt.includes('uint')) return 'Numerico (intero)';
  if (dt.includes('float') || dt.includes('decimal')) return 'Numerico (reale)';
  if (dt.includes('bool')) return 'Booleano';
  if (dt.includes('datetime') || dt.includes('date')) return 'Datetime';
  if (dt.includes('utf8') || dt.includes('string')) return 'Testo';

  return dtypeOriginal ? String(dtypeOriginal) : 'Sconosciuto';
}

function getColumnGroup(column) {
  const semanticType = column?.semantic_type || '';
  if (semanticType.startsWith('numeric')) return 'numeric';
  if (semanticType.startsWith('categorical') || semanticType === 'boolean') return 'categorical';
  if (semanticType === 'datetime') return 'datetime';
  return 'text';
}

function stringifyValue(value) {
  if (value === null || value === undefined) return 'null';
  if (value === '') return '(stringa vuota)';
  return String(value);
}

function summarizeSample(values) {
  const normalized = values.map(stringifyValue);
  const counts = new Map();
  normalized.forEach(value => {
    counts.set(value, (counts.get(value) || 0) + 1);
  });

  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value))
    .slice(0, 10);
}

export function OverviewSection({ data, analysisId }) {
  const columns = data?.columns || [];
  const [group, setGroup] = useState('all');
  const [selectedColumn, setSelectedColumn] = useState(columns[0]?.name || null);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleError, setSampleError] = useState(null);
  const [sampleValues, setSampleValues] = useState([]);

  useEffect(() => {
    if (!columns.length) {
      setSelectedColumn(null);
      return;
    }

    setSelectedColumn(prev => {
      if (prev && columns.some(column => column.name === prev)) return prev;
      return columns[0]?.name || null;
    });
  }, [columns]);

  const filteredColumns = useMemo(
    () => columns.filter(column => group === 'all' || getColumnGroup(column) === group),
    [columns, group],
  );

  const activeColumn = useMemo(
    () => filteredColumns.find(column => column.name === selectedColumn) || filteredColumns[0] || null,
    [filteredColumns, selectedColumn],
  );

  const groupCounts = useMemo(() => {
    const counts = { all: columns.length, numeric: 0, categorical: 0, datetime: 0, text: 0 };
    columns.forEach(column => {
      counts[getColumnGroup(column)] += 1;
    });
    return counts;
  }, [columns]);

  useEffect(() => {
    if (!analysisId || !activeColumn?.name) {
      setSampleValues([]);
      return;
    }

    let active = true;
    setSampleLoading(true);
    setSampleError(null);

    analysisApi.sampleData(analysisId, { columns: [activeColumn.name] })
      .then(({ data: payload }) => {
        if (!active) return;
        setSampleValues(payload?.columns?.[activeColumn.name] || []);
      })
      .catch(error => {
        if (!active) return;
        const message = error?.response?.data?.detail || error?.message || 'Errore nel recupero del campione colonna.';
        setSampleError(String(message));
        setSampleValues([]);
      })
      .finally(() => {
        if (active) setSampleLoading(false);
      });

    return () => {
      active = false;
    };
  }, [activeColumn?.name, analysisId]);

  const frequencies = useMemo(() => summarizeSample(sampleValues), [sampleValues]);
  const previewRows = useMemo(
    () => sampleValues.slice(0, 12).map((value, index) => ({ index: index + 1, value: stringifyValue(value) })),
    [sampleValues],
  );
  const uniquePreview = useMemo(
    () => Array.from(new Set(sampleValues.map(stringifyValue))).slice(0, 12),
    [sampleValues],
  );

  if (!data) return null;

  return (
    <div className="u-flex u-flex-col u-gap-6">
      <div className="u-flex u-gap-4 u-flex-wrap">
        <StatCard label="Righe" value={data.n_rows?.toLocaleString('it-IT')} />
        <StatCard label="Colonne" value={data.n_cols} />
        <StatCard label="Celle" value={data.n_cells?.toLocaleString('it-IT')} />
        <StatCard label="Memoria" value={data.memory_mb} unit="MB" />
        <StatCard
          label="Missing %"
          value={data.pct_missing_global}
          unit="%"
          accent={data.pct_missing_global > 20}
        />
      </div>

      {data.notes?.length > 0 && (
        <div className="u-flex u-flex-col u-gap-2">
          {data.notes.map((n, i) => (
            <div key={i} className="alert alert--error">
              <span>⚠</span>
              <span>{n}</span>
            </div>
          ))}
        </div>
      )}

      {data.charts?.types_distribution && (
        <div className="card">
          <PlotlyChart chart={data.charts.types_distribution} height={320} />
        </div>
      )}

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Analisi colonna per colonna</h3>
            <p className="card__subtitle">Esplora una colonna alla volta con frequenze, valori distinti e preview del campione.</p>
          </div>
        </div>

        <div className="tabs__nav" role="tablist">
          {COLUMN_GROUPS.filter(item => item.key === 'all' || groupCounts[item.key] > 0).map(item => (
            <button
              key={item.key}
              role="tab"
              aria-selected={group === item.key}
              className={`tab${group === item.key ? ' tab--active' : ''}`}
              onClick={() => setGroup(item.key)}
            >
              {item.label}
              <span className="badge badge--neutral u-ml-2">{groupCounts[item.key]}</span>
            </button>
          ))}
        </div>

        <div className="uni-layout u-mt-4">
          <aside className="uni-sidebar">
            {filteredColumns.map(column => (
              <button
                key={column.name}
                className={`uni-col-btn${activeColumn?.name === column.name ? ' uni-col-btn--active' : ''}`}
                onClick={() => setSelectedColumn(column.name)}
              >
                <span className="uni-col-name">{column.name}</span>
                <span className="uni-col-type">{column.semantic_type}</span>
              </button>
            ))}
          </aside>

          <div className="uni-content">
            {activeColumn && (
              <div className="u-flex u-flex-col u-gap-4">
                <div className="u-flex u-items-center u-gap-3">
                  <h3 className="u-text-lg u-font-semibold u-text-primary">{activeColumn.name}</h3>
                  <span className="badge badge--neutral">{activeColumn.semantic_type}</span>
                  <span className="badge badge--neutral">{formatTechnicalType(activeColumn.dtype_original, activeColumn.semantic_type)}</span>
                </div>

                <div className="u-flex u-gap-4 u-flex-wrap">
                  <StatCard label="Valori unici" value={activeColumn.n_unique} />
                  <StatCard label="Missing %" value={activeColumn.pct_missing} unit="%" accent={activeColumn.pct_missing > 20} />
                  <StatCard label="Gruppo" value={getColumnGroup(activeColumn)} />
                </div>

                {sampleLoading ? (
                  <div className="card">
                    <div className="empty-state">
                      <Spinner size={32} />
                      <p className="u-text-secondary u-mt-4">Recupero campione colonna...</p>
                    </div>
                  </div>
                ) : sampleError ? (
                  <div className="alert alert--error">
                    <span>⚠</span>
                    <span>{sampleError}</span>
                  </div>
                ) : (
                  <>
                    <div className="u-flex u-gap-4 u-flex-wrap">
                      <div className="card u-flex-1" style={{ minWidth: 300 }}>
                        <div className="card__header">
                          <div className="card__header-left">
                            <h4 className="card__title">Valori distinti (campione)</h4>
                            <p className="card__subtitle">{uniquePreview.length} mostrati</p>
                          </div>
                        </div>
                        <div className="cleaning-chip-row">
                          {uniquePreview.length > 0 ? uniquePreview.map(value => (
                            <span key={value} className="cleaning-chip" style={{ fontFamily: 'var(--font-mono)' }}>
                              {value}
                            </span>
                          )) : (
                            <span className="u-text-secondary u-text-sm">Nessun valore disponibile nel campione.</span>
                          )}
                        </div>
                      </div>

                      <div className="card u-flex-1" style={{ minWidth: 300 }}>
                        <div className="card__header">
                          <div className="card__header-left">
                            <h4 className="card__title">Frequenze principali</h4>
                            <p className="card__subtitle">Top 10 dal campione recuperato</p>
                          </div>
                        </div>
                        <div className="table-container">
                          <table className="table">
                            <thead>
                              <tr>
                                <th>Valore</th>
                                <th className="numeric">Frequenza</th>
                              </tr>
                            </thead>
                            <tbody>
                              {frequencies.length > 0 ? frequencies.map(row => (
                                <tr key={row.value}>
                                  <td style={{ fontFamily: 'var(--font-mono)' }}>{row.value}</td>
                                  <td className="numeric">{row.count}</td>
                                </tr>
                              )) : (
                                <tr>
                                  <td colSpan={2} className="u-text-secondary u-text-sm">Nessuna frequenza disponibile.</td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>

                    <div className="card">
                      <div className="card__header">
                        <div className="card__header-left">
                          <h4 className="card__title">Preview dati</h4>
                          <p className="card__subtitle">Prime 12 osservazioni del campione usato per l’analisi.</p>
                        </div>
                      </div>
                      <div className="table-container">
                        <table className="table">
                          <thead>
                            <tr>
                              <th>#</th>
                              <th>Valore</th>
                            </tr>
                          </thead>
                          <tbody>
                            {previewRows.length > 0 ? previewRows.map(row => (
                              <tr key={`${activeColumn.name}-${row.index}`}>
                                <td className="numeric">{row.index}</td>
                                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.value}</td>
                              </tr>
                            )) : (
                              <tr>
                                <td colSpan={2} className="u-text-secondary u-text-sm">Nessun dato disponibile nel campione.</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card__header">
          <div className="card__header-left">
            <h3 className="card__title">Struttura colonne</h3>
            <p className="card__subtitle">{columns.length} colonne</p>
          </div>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Tipo semantico</th>
                <th>Tipo reale</th>
                <th>Ruolo</th>
                <th className="numeric">Unici</th>
                <th className="numeric">Missing %</th>
              </tr>
            </thead>
            <tbody>
              {columns.map(c => (
                <tr key={c.name}>
                  <td className="u-font-medium">{c.name}</td>
                  <td>
                    <span className="badge badge--neutral">{c.semantic_type}</span>
                  </td>
                  <td>
                    <span className="badge badge--neutral">
                      {formatTechnicalType(c.dtype_original, c.semantic_type)}
                    </span>
                  </td>
                  <td className="u-text-secondary">{c.role}</td>
                  <td className="numeric">{c.n_unique}</td>
                  <td className="numeric">{c.pct_missing}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
