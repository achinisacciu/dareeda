export function StatCard({ label, value, accent = false, unit = '', trend = null, loading = false }) {
  const formatValue = (val) => {
    if (typeof val !== 'number') return val;
    if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M';
    if (val >= 1000) return (val / 1000).toFixed(1) + 'K';
    return val.toLocaleString();
  };

  const displayValue = formatValue(value);

  return (
    <div
      className={`stat-card${accent ? ' stat-card--accent' : ''}`}
      role="region"
      aria-label={`Statistiche: ${label}`}
    >
      <div className="stat-card__head">
        <div className="stat-card__label">{label}</div>
        {trend !== null && !loading && (
          <div
            className={`stat-card__trend${trend >= 0 ? ' stat-card__trend--up' : ' stat-card__trend--down'}`}
            aria-label={`Trend: ${trend >= 0 ? 'In aumento' : 'In diminuzione'} ${Math.abs(trend)}%`}
          >
            {trend >= 0 ? '+' : '-'} {Math.abs(trend)}%
          </div>
        )}
      </div>

      <div className="stat-card__value">
        {loading ? (
          <span className="skeleton skeleton--text" aria-hidden="true" style={{ width: 60 }} />
        ) : (
          <>
            {displayValue}
            {unit && <small className="stat-card__unit">{unit}</small>}
          </>
        )}
      </div>
    </div>
  );
}
