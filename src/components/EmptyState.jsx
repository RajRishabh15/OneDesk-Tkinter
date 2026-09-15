export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-[var(--color-line)] dark:border-[var(--color-line-dark)] py-16 px-6 text-center animate-fade-up">
      {Icon && (
        <div className="grid h-12 w-12 place-items-center rounded-full bg-[var(--color-accent-soft)] dark:bg-white/5 text-[var(--color-accent)]">
          <Icon size={22} />
        </div>
      )}
      <p className="font-display text-base font-semibold">{title}</p>
      {description && (
        <p className="max-w-sm text-sm text-[var(--color-ink-soft)] dark:text-[var(--color-ink-dark-soft)]">
          {description}
        </p>
      )}
      {action}
    </div>
  );
}
