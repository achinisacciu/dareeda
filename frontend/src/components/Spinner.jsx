export function Spinner({
  size = 24,
  variant = 'primary',
  speed = 'normal',
  label = 'Caricamento...',
  centered = false
}) {
  const sizeNum = typeof size === 'number' ? size : parseInt(size, 10);

  const variants = {
    primary: { border: 'rgba(89,173,247,0.2)',  top: 'var(--color-ocean-500)' },
    accent:  { border: 'rgba(228,0,43,0.2)',    top: 'var(--color-primary-500)' },
    light:   { border: 'rgba(255,255,255,0.2)', top: '#FFFFFF' },
    dark:    { border: 'rgba(0,0,0,0.1)',       top: 'var(--color-neutral-800)' },
  };

  const speeds = { slow: '1.5s', normal: '0.8s', fast: '0.5s' };

  const spinnerStyle = {
    width: sizeNum,
    height: sizeNum,
    borderWidth: Math.max(2, Math.floor(sizeNum / 8)),
    borderStyle: 'solid',
    borderColor: variants[variant]?.border || variants.primary.border,
    borderTopColor: variants[variant]?.top || variants.primary.top,
    animationDuration: speeds[speed] || speeds.normal,
  };

  return (
    <span
      className={`spinner-wrapper${centered ? ' spinner-wrapper--centered' : ''}`}
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <span className="spinner" style={spinnerStyle} aria-hidden="true" />
      {centered && <span className="spinner__label">{label}</span>}
    </span>
  );
}

export const SpinnerAccent = (props) => <Spinner {...props} variant="accent" />;
export const SpinnerLight  = (props) => <Spinner {...props} variant="light" />;
export const SpinnerDark   = (props) => <Spinner {...props} variant="dark" />;
