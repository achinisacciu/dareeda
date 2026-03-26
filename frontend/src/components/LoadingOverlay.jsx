import { SpinnerAccent } from './Spinner';

export function LoadingOverlay({
  open = false,
  title = 'Elaborazione in corso',
  description = 'Attendi il completamento dell’operazione.',
}) {
  if (!open) return null;

  return (
    <div className="loading-overlay" role="status" aria-live="polite" aria-busy="true">
      <div className="loading-overlay__panel">
        <SpinnerAccent size={40} />
        <div className="loading-overlay__title">{title}</div>
        <div className="loading-overlay__description">{description}</div>
      </div>
    </div>
  );
}
