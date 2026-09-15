import { Pin, Pencil, Trash2 } from 'lucide-react';
import Card from './Card';

const colorStyles = {
  violet: 'border-t-2 border-t-stone-800 dark:border-t-stone-200',
  cyan: 'border-t-2 border-t-sky-600 dark:border-t-sky-400',
  green: 'border-t-2 border-t-emerald-600 dark:border-t-emerald-400',
  amber: 'border-t-2 border-t-amber-600 dark:border-t-amber-400',
  rose: 'border-t-2 border-t-rose-600 dark:border-t-rose-400',
};

function relativeDate(iso) {
  const date = new Date(iso);
  const today = new Date();
  const diffDays = Math.round((today.setHours(0, 0, 0, 0) - new Date(date).setHours(0, 0, 0, 0)) / 86400000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 0) return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  return `${diffDays}d ago`;
}

export default function NoteCard({ note, onEdit, onDelete, onTogglePin }) {
  return (
    <Card className={`flex flex-col justify-between gap-3 p-4 transition-all duration-150 hover:border-stone-300 dark:hover:border-stone-700 ${colorStyles[note.color] || colorStyles.violet}`}>
      <div>
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <h3 className="font-display text-sm font-bold text-stone-900 dark:text-stone-100 leading-snug tracking-tight">{note.title}</h3>
          <button
            onClick={() => onTogglePin(note.id)}
            aria-label={note.pinned ? 'Unpin note' : 'Pin note'}
            className={note.pinned ? 'text-stone-900 dark:text-stone-100' : 'text-stone-300 hover:text-stone-500 dark:text-stone-600 dark:hover:text-stone-400'}
          >
            <Pin size={14} fill={note.pinned ? 'currentColor' : 'none'} />
          </button>
        </div>

        <p className="whitespace-pre-line text-xs text-stone-600 dark:text-stone-300 line-clamp-4 leading-relaxed font-sans">
          {note.description}
        </p>
      </div>

      <div>
        {note.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2.5">
            {note.tags.map((tag) => (
              <span key={tag} className="rounded px-1.5 py-0.5 text-[10px] font-mono font-medium bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400">
                #{tag}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-stone-100 dark:border-stone-800/80 text-[10px] text-stone-400 font-mono">
          <span>{relativeDate(note.createdAt)}</span>
          <div className="flex gap-0.5">
            <button
              onClick={() => onEdit(note)}
              aria-label="Edit note"
              className="rounded p-1 hover:bg-stone-100 hover:text-stone-700 dark:hover:bg-stone-800 dark:hover:text-stone-200 transition-colors"
            >
              <Pencil size={12} />
            </button>
            <button
              onClick={() => onDelete(note.id)}
              aria-label="Delete note"
              className="rounded p-1 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 transition-colors"
            >
              <Trash2 size={12} />
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}
