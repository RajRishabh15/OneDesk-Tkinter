import { useMemo, useState } from 'react';
import { Plus, CheckSquare, LayoutGrid, Rows3 } from 'lucide-react';
import Modal from '../components/Modal';
import TaskCard from '../components/TaskCard';
import EmptyState from '../components/EmptyState';
import { useData } from '../context/DataContext';
import { LabeledInput } from './Notes';

const columns = ['Todo', 'In Progress', 'Completed'];
const emptyForm = { title: '', description: '', priority: 'Medium', dueDate: '', category: '', status: 'Todo' };

export default function Tasks() {
  const { tasks, addTask, updateTask, deleteTask, setTaskStatus } = useData();
  const [view, setView] = useState('list');
  const [filter, setFilter] = useState('All');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [dragId, setDragId] = useState(null);
  const [inlineTask, setInlineTask] = useState('');

  const filtered = useMemo(() => {
    if (filter === 'All') return tasks;
    return tasks.filter((t) => t.status === filter);
  }, [tasks, filter]);

  const completedCount = tasks.filter((t) => t.status === 'Completed').length;
  const pct = tasks.length ? Math.round((completedCount / tasks.length) * 100) : 0;

  function openNew() {
    setEditing(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(task) {
    setEditing(task);
    setForm(task);
    setModalOpen(true);
  }

  function handleSubmit(e) {
    e.preventDefault();
    const payload = { ...form, title: form.title.trim() };
    if (editing) updateTask(editing.id, payload);
    else addTask(payload);
    setModalOpen(false);
  }

  function handleInlineAdd(e) {
    e.preventDefault();
    if (!inlineTask.trim()) return;
    addTask({
      title: inlineTask.trim(),
      priority: 'Medium',
      dueDate: new Date().toISOString().slice(0, 10),
      status: filter === 'Completed' ? 'Completed' : filter === 'In Progress' ? 'In Progress' : 'Todo',
      category: 'General',
    });
    setInlineTask('');
  }

  function toggleComplete(task) {
    setTaskStatus(task.id, task.status === 'Completed' ? 'Todo' : 'Completed');
  }

  return (
    <div className="space-y-5 animate-fade-up max-w-6xl mx-auto pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-stone-200/80 dark:border-stone-800/80 pb-4">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-100">Tasks</h1>
          <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
            {completedCount} of {tasks.length} tasks completed ({pct}%)
          </p>
        </div>
        <button
          onClick={openNew}
          className="flex items-center gap-1.5 rounded-lg bg-stone-900 hover:bg-stone-800 dark:bg-stone-100 dark:hover:bg-white dark:text-stone-900 text-stone-100 px-3 py-1.5 text-xs font-semibold shadow-xs transition-colors"
        >
          <Plus size={13} /> Detailed task
        </button>
      </div>

      {/* Filter and View Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {['All', ...columns].map((c) => (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className={[
                'rounded-lg px-2.5 py-1 text-xs font-medium transition-colors',
                filter === c
                  ? 'bg-stone-900 text-stone-100 dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                  : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-400 hover:bg-stone-100/60 dark:hover:bg-stone-800/60',
              ].join(' ')}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="flex rounded-lg border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 p-0.5">
          <button
            onClick={() => setView('list')}
            aria-label="List view"
            className={`rounded-md p-1.5 transition-colors ${view === 'list' ? 'bg-stone-200/80 dark:bg-stone-800 text-stone-900 dark:text-stone-100' : 'text-stone-400 hover:text-stone-700'}`}
          >
            <Rows3 size={14} />
          </button>
          <button
            onClick={() => setView('kanban')}
            aria-label="Kanban view"
            className={`rounded-md p-1.5 transition-colors ${view === 'kanban' ? 'bg-stone-200/80 dark:bg-stone-800 text-stone-900 dark:text-stone-100' : 'text-stone-400 hover:text-stone-700'}`}
          >
            <LayoutGrid size={14} />
          </button>
        </div>
      </div>

      {/* Things 3 Style Inline Task Input */}
      <form
        onSubmit={handleInlineAdd}
        className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1a1a18] shadow-[0_1px_2px_rgba(0,0,0,0.02)] focus-within:border-stone-400 dark:focus-within:border-stone-600 transition-all"
      >
        <div className="h-4 w-4 rounded-full border border-dashed border-stone-300 dark:border-stone-600 flex items-center justify-center shrink-0">
          <Plus size={10} className="text-stone-400" />
        </div>
        <input
          type="text"
          value={inlineTask}
          onChange={(e) => setInlineTask(e.target.value)}
          placeholder="Add a new task... (Type and press Enter)"
          className="w-full text-xs sm:text-sm bg-transparent outline-none placeholder:text-stone-400 text-stone-900 dark:text-stone-100"
        />
        {inlineTask.trim() && (
          <button
            type="submit"
            className="shrink-0 text-xs font-semibold bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 px-2.5 py-1 rounded-md"
          >
            Add
          </button>
        )}
      </form>

      {/* Task Content */}
      {tasks.length === 0 ? (
        <EmptyState icon={CheckSquare} title="No tasks yet" description="Type above or click Detailed task to begin." />
      ) : view === 'list' ? (
        filtered.length === 0 ? (
          <EmptyState icon={CheckSquare} title="No matching tasks" description="Try selecting a different filter tab." />
        ) : (
          <div className="space-y-2">
            {filtered.map((task) => (
              <TaskCard key={task.id} task={task} onToggleComplete={toggleComplete} onEdit={openEdit} onDelete={deleteTask} />
            ))}
          </div>
        )
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {columns.map((col) => {
            const colTasks = tasks.filter((t) => t.status === col);
            return (
              <div
                key={col}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  if (dragId) setTaskStatus(dragId, col);
                  setDragId(null);
                }}
                className="min-h-[220px] rounded-xl bg-stone-50/60 dark:bg-stone-900/40 border border-stone-200/80 dark:border-stone-800 p-3 flex flex-col"
              >
                <div className="mb-2.5 flex items-center justify-between px-1">
                  <p className="text-xs font-bold text-stone-700 dark:text-stone-300 uppercase tracking-wider font-mono">{col}</p>
                  <span className="rounded-md bg-white dark:bg-stone-800 border border-stone-200/80 dark:border-stone-700 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-stone-500">
                    {colTasks.length}
                  </span>
                </div>
                <div className="space-y-2 flex-1">
                  {colTasks.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      draggable
                      onDragStart={() => setDragId(task.id)}
                      onToggleComplete={toggleComplete}
                      onEdit={openEdit}
                      onDelete={deleteTask}
                    />
                  ))}
                  {colTasks.length === 0 && (
                    <div className="h-24 grid place-items-center border border-dashed border-stone-200 dark:border-stone-800 rounded-lg text-xs text-stone-400">
                      Drop tasks here
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal for detailed task configuration */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit task' : 'New task'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <LabeledInput label="Task title" required value={form.title} onChange={(v) => setForm((f) => ({ ...f, title: v }))} placeholder="Task title..." />
          <div>
            <label className="mb-1 block text-xs font-semibold text-stone-600 dark:text-stone-300">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={3}
              placeholder="Add extra details..."
              className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-900 p-2.5 text-xs outline-none transition-all placeholder:text-stone-400 focus:bg-white dark:focus:bg-stone-900 focus:border-stone-400"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-stone-600 dark:text-stone-300">Priority</label>
              <select
                value={form.priority}
                onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-900 px-2.5 py-1.5 text-xs outline-none focus:border-stone-400"
              >
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-stone-600 dark:text-stone-300">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-900 px-2.5 py-1.5 text-xs outline-none focus:border-stone-400"
              >
                {columns.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <LabeledInput label="Due date" type="date" value={form.dueDate} onChange={(v) => setForm((f) => ({ ...f, dueDate: v }))} />
            <LabeledInput label="Category" placeholder="e.g. Work, Personal" value={form.category} onChange={(v) => setForm((f) => ({ ...f, category: v }))} />
          </div>
          <div className="flex justify-end gap-2 pt-3 border-t border-stone-100 dark:border-stone-800">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="rounded-lg border border-stone-200 dark:border-stone-800 px-3 py-1.5 text-xs font-medium text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-stone-900 hover:bg-stone-800 dark:bg-stone-100 dark:hover:bg-white dark:text-stone-900 text-stone-100 px-3.5 py-1.5 text-xs font-semibold shadow-xs transition-colors"
            >
              {editing ? 'Save changes' : 'Add task'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
