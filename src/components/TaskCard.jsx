import { Calendar, Trash2, Pencil, Check } from 'lucide-react';
import Card from './Card';

const priorityConfig = {
  High: { dot: 'bg-rose-500', label: 'High', color: 'text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 border-rose-200/60 dark:border-rose-900/30' },
  Medium: { dot: 'bg-amber-500', label: 'Med', color: 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border-amber-200/60 dark:border-amber-900/30' },
  Low: { dot: 'bg-emerald-500', label: 'Low', color: 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200/60 dark:border-emerald-900/30' },
};

function formatDue(dateStr) {
  if (!dateStr) return null;
  const date = new Date(dateStr + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.round((date - today) / 86400000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  if (diffDays === -1) return 'Yesterday';
  if (diffDays < 0) return `${Math.abs(diffDays)}d overdue`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function TaskCard({ task, onToggleComplete, onEdit, onDelete, draggable, onDragStart }) {
  const priority = priorityConfig[task.priority] || priorityConfig.Medium;
  const due = formatDue(task.dueDate);
  const overdue = task.status !== 'Completed' && due?.includes('overdue');
  const isCompleted = task.status === 'Completed';

  return (
    <Card
      className={`p-3 group transition-all duration-150 ${isCompleted ? 'opacity-60 bg-stone-50/60 dark:bg-stone-900/30' : 'hover:border-stone-300 dark:hover:border-stone-700'}`}
      draggable={draggable}
      onDragStart={onDragStart}
    >
      <div className="flex items-start gap-3">
        {/* Tactile Circular Checkbox */}
        <button
          onClick={() => onToggleComplete(task)}
          aria-label={isCompleted ? 'Mark as not complete' : 'Mark as complete'}
          className={[
            'mt-0.5 h-4 w-4 shrink-0 rounded-full border flex items-center justify-center transition-all duration-150',
            isCompleted
              ? 'border-stone-900 bg-stone-900 dark:border-stone-200 dark:bg-stone-200 text-white dark:text-stone-900'
              : 'border-stone-300 dark:border-stone-600 hover:border-stone-500 bg-white dark:bg-stone-800',
          ].join(' ')}
        >
          {isCompleted && <Check size={10} strokeWidth={3} />}
        </button>

        <div className="min-w-0 flex-1">
          <p className={['text-xs sm:text-sm font-medium tracking-tight', isCompleted ? 'line-through text-stone-400 dark:text-stone-500' : 'text-stone-900 dark:text-stone-100'].join(' ')}>
            {task.title}
          </p>
          {task.description && (
            <p className="mt-1 text-xs text-stone-500 dark:text-stone-400 line-clamp-2 leading-relaxed">{task.description}</p>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium border ${priority.color}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${priority.dot}`} />
              {priority.label}
            </span>
            {due && (
              <span className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-mono font-medium border ${overdue ? 'bg-rose-50 text-rose-700 border-rose-200/60 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/30' : 'bg-stone-100 text-stone-600 border-stone-200 dark:bg-stone-800 dark:text-stone-300 dark:border-stone-700'}`}>
                <Calendar size={10} /> {due}
              </span>
            )}
            {task.category && (
              <span className="rounded-md bg-stone-100 dark:bg-stone-800/80 px-1.5 py-0.5 text-[10px] font-medium text-stone-500 dark:text-stone-400">
                {task.category}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex shrink-0 gap-0.5 opacity-80 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onEdit(task)}
            aria-label="Edit task"
            className="rounded-md p-1 text-stone-400 hover:text-stone-700 hover:bg-stone-100 dark:hover:text-stone-200 dark:hover:bg-stone-800 transition-colors"
          >
            <Pencil size={12} />
          </button>
          <button
            onClick={() => onDelete(task.id)}
            aria-label="Delete task"
            className="rounded-md p-1 text-stone-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>
    </Card>
  );
}
