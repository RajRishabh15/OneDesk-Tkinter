import { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Modal({ open, onClose, title, children, wide = false }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose?.();
    }
    if (open) document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-stone-950/40 backdrop-blur-xs animate-fade-up"
        onClick={onClose}
      />
      <div
        className={[
          'relative w-full rounded-2xl border border-stone-200/90 dark:border-stone-800/90',
          'bg-white dark:bg-[#191917] shadow-2xl animate-fade-up max-h-[90vh] overflow-y-auto',
          wide ? 'max-w-2xl' : 'max-w-md',
        ].join(' ')}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-stone-200/70 dark:border-stone-800/70">
          <h2 className="font-display text-base font-semibold tracking-tight text-stone-900 dark:text-stone-100">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-800 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
