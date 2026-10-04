export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="state-block">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-block state-error">
      <p>⚠ {message}</p>
      {onRetry && <button onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function EmptyState({ message, icon = "📭" }: { message: string; icon?: string }) {
  return (
    <div className="state-block state-empty">
      <span className="state-icon">{icon}</span>
      <p>{message}</p>
    </div>
  );
}
