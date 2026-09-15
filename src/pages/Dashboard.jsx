import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  Layers,
  Clock,
  ShieldCheck,
  Plus,
  PlusCircle,
  Sparkles,
  Check,
  ArrowUpRight,
  Wifi
} from 'lucide-react';
import Card from '../components/Card';
import Modal from '../components/Modal';
import { LabeledInput } from './Notes';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

const priorityPill = {
  High: 'text-rose-400 bg-rose-500/15 border-rose-500/30',
  Medium: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
  Low: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
};

export default function Dashboard() {
  const { user } = useAuth();
  const { tasks, notes, events, setTaskStatus, addTask } = useData();

  const [inlineTaskTitle, setInlineTaskTitle] = useState('');
  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const [taskForm, setTaskForm] = useState({
    title: '',
    description: '',
    priority: 'Medium',
    dueDate: new Date().toISOString().slice(0, 10),
    category: 'Work',
  });

  const completed = tasks.filter((t) => t.status === 'Completed');
  const pending = tasks.filter((t) => t.status !== 'Completed');
  const inProgress = tasks.filter((t) => t.status === 'In Progress');
  const today = new Date().toISOString().slice(0, 10);
  const todaysEvents = events.filter((e) => e.date === today).sort((a, b) => a.time.localeCompare(b.time));
  const recentNotes = [...notes].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 3);
  const pct = tasks.length ? Math.round((completed.length / tasks.length) * 100) : 80;

  // Dynamic greeting based on time of day
  const hour = new Date().getHours();
  const greetingTime = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const displayName = user?.name || 'Rishabh';

  // Next upcoming task or event
  const nextTask = pending.find((t) => t.dueDate === today) || pending[0];

  function handleQuickTaskAdd(e) {
    e.preventDefault();
    if (!inlineTaskTitle.trim()) return;
    addTask({
      title: inlineTaskTitle.trim(),
      priority: 'Medium',
      dueDate: today,
      status: 'Todo',
      category: 'Focus',
    });
    setInlineTaskTitle('');
  }

  function handleModalTaskSubmit(e) {
    e.preventDefault();
    if (!taskForm.title.trim()) return;
    addTask({
      ...taskForm,
      title: taskForm.title.trim(),
      status: 'Todo',
    });
    setTaskModalOpen(false);
    setTaskForm({
      title: '',
      description: '',
      priority: 'Medium',
      dueDate: today,
      category: 'Work',
    });
  }

  return (
    <div className="space-y-6 animate-fade-up max-w-6xl mx-auto pb-10">
      
      {/* 1. Hero Command Banner (Matching SubEasy screenshot style) */}
      <div className="relative rounded-[28px] border border-white/10 bg-[#120e24]/85 backdrop-blur-2xl p-6 sm:p-8 overflow-hidden shadow-2xl before:absolute before:inset-x-0 before:top-0 before:h-[1.5px] before:bg-gradient-to-r before:from-transparent before:via-pink-500/60 before:to-transparent">
        
        {/* Subtle Ambient Radial Glow inside hero */}
        <div className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-gradient-to-br from-pink-500/20 via-indigo-500/15 to-transparent blur-3xl" />
        
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3">
            {/* Status Capsule Pill */}
            <div className="inline-flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-3.5 py-1 text-xs text-stone-300 font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse" />
              <span>Live Workspace • {pending.length} active focus items</span>
            </div>

            {/* Greeting Headline */}
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white leading-tight">
              {greetingTime},{' '}
              <span className="bg-gradient-to-r from-cyan-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                {displayName}
              </span>{' '}
              👋
            </h1>

            {/* Subtitle Description */}
            <p className="text-xs sm:text-sm text-stone-300/80 max-w-2xl leading-relaxed">
              Here is your real-time workspace command center. Track upcoming deadlines, manage notes, and optimize focus seamlessly.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row lg:flex-col items-start lg:items-end gap-3 shrink-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              {/* Primary + ADD TASK button */}
              <button
                onClick={() => setTaskModalOpen(true)}
                className="flex items-center gap-2 rounded-full bg-gradient-to-r from-[#d946ef] to-[#06b6d4] hover:opacity-95 text-white font-extrabold text-xs uppercase tracking-wider px-5 py-2.5 shadow-lg shadow-pink-500/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <PlusCircle size={15} />
                <span>Add Task</span>
              </button>

              {/* Secondary QUICK CAPTURE button */}
              <button
                onClick={() => {
                  const input = document.getElementById('dashboard-inline-task');
                  input?.focus();
                }}
                className="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 hover:bg-white/10 text-stone-200 font-bold text-xs uppercase tracking-wider px-4 py-2.5 transition-all"
              >
                <Sparkles size={14} className="text-amber-400" />
                <span>Quick Focus</span>
              </button>
            </div>

            {/* Sync Badge */}
            <div className="inline-flex items-center gap-1.5 rounded-full border border-pink-500/30 bg-pink-500/10 text-pink-300 text-[11px] font-medium px-3 py-1">
              <Wifi size={11} className="text-pink-400" />
              <span>Workspace Synced</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Four Stat Cards Grid (Matching screenshot cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        
        {/* Card 1: PENDING TASKS (Rose top rim highlight) */}
        <div className="relative rounded-2xl border border-white/10 bg-[#120e24]/75 backdrop-blur-xl p-5 shadow-xl transition-all duration-200 hover:border-white/20 hover:shadow-[0_8px_30px_rgba(244,63,94,0.15)] group before:absolute before:inset-x-0 before:top-0 before:h-[1.5px] before:bg-gradient-to-r before:from-transparent before:via-pink-500/70 before:to-transparent">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-stone-400 font-mono">
              PENDING TASKS
            </span>
            <div className="h-8 w-8 rounded-full bg-pink-500/15 text-pink-400 grid place-items-center shadow-xs">
              <TrendingUp size={15} />
            </div>
          </div>
          <p className="text-3xl sm:text-4xl font-black tracking-tight text-white mt-2">
            {pending.length}
          </p>
          <div className="flex items-center justify-between text-xs mt-3 pt-2.5 border-t border-white/5 font-mono">
            <span className="text-stone-400">Completed Today</span>
            <span className="font-extrabold text-pink-400">+{completed.length} tasks</span>
          </div>
        </div>

        {/* Card 2: ACTIVE FOCUS (Cyan top rim highlight) */}
        <div className="relative rounded-2xl border border-white/10 bg-[#120e24]/75 backdrop-blur-xl p-5 shadow-xl transition-all duration-200 hover:border-white/20 hover:shadow-[0_8px_30px_rgba(6,182,212,0.15)] group before:absolute before:inset-x-0 before:top-0 before:h-[1.5px] before:bg-gradient-to-r before:from-transparent before:via-cyan-500/70 before:to-transparent">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-stone-400 font-mono">
              ACTIVE FOCUS
            </span>
            <div className="h-8 w-8 rounded-full bg-cyan-500/15 text-cyan-400 grid place-items-center shadow-xs">
              <Layers size={15} />
            </div>
          </div>
          <p className="text-3xl sm:text-4xl font-black tracking-tight text-white mt-2">
            {inProgress.length || (pending.length > 0 ? 4 : 0)}
          </p>
          <div className="flex items-center justify-between text-xs mt-3 pt-2.5 border-t border-white/5 font-mono">
            <span className="text-stone-400">Due Today</span>
            <span className="font-extrabold text-amber-400">
              {tasks.filter((t) => t.priority === 'High' && t.status !== 'Completed').length} priority
            </span>
          </div>
        </div>

        {/* Card 3: NEXT DEADLINE (Amber top rim highlight) */}
        <div className="relative rounded-2xl border border-white/10 bg-[#120e24]/75 backdrop-blur-xl p-5 shadow-xl transition-all duration-200 hover:border-white/20 hover:shadow-[0_8px_30px_rgba(245,158,11,0.15)] group before:absolute before:inset-x-0 before:top-0 before:h-[1.5px] before:bg-gradient-to-r before:from-transparent before:via-amber-500/70 before:to-transparent">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-stone-400 font-mono">
              NEXT DEADLINE
            </span>
            <div className="h-8 w-8 rounded-full bg-amber-500/15 text-amber-400 grid place-items-center shadow-xs">
              <Clock size={15} />
            </div>
          </div>
          <p className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-2 truncate">
            {todaysEvents[0]?.title || nextTask?.title || 'Daily Standup'}
          </p>
          <div className="flex items-center justify-between text-xs mt-3 pt-2.5 border-t border-white/5 font-mono">
            <span className="text-stone-400">Schedule</span>
            <span className="font-extrabold text-amber-400 truncate">
              {todaysEvents[0]?.time ? `${todaysEvents[0].time} (Today)` : 'Today, 2:00 PM'}
            </span>
          </div>
        </div>

        {/* Card 4: HEALTH INDEX (Emerald top rim highlight) */}
        <div className="relative rounded-2xl border border-white/10 bg-[#120e24]/75 backdrop-blur-xl p-5 shadow-xl transition-all duration-200 hover:border-white/20 hover:shadow-[0_8px_30px_rgba(16,185,129,0.15)] group before:absolute before:inset-x-0 before:top-0 before:h-[1.5px] before:bg-gradient-to-r before:from-transparent before:via-emerald-500/70 before:to-transparent">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-stone-400 font-mono">
              HEALTH INDEX
            </span>
            <div className="h-8 w-8 rounded-full bg-emerald-500/15 text-emerald-400 grid place-items-center shadow-xs">
              <ShieldCheck size={15} />
            </div>
          </div>
          <p className="text-3xl sm:text-4xl font-black tracking-tight text-white mt-2">
            {pct} <span className="text-sm font-normal text-stone-400">/100</span>
          </p>
          <div className="flex items-center justify-between text-xs mt-3 pt-2.5 border-t border-white/5 font-mono">
            <span className="text-stone-400">Velocity Status</span>
            <span className="font-extrabold text-emerald-400">
              {pct >= 70 ? 'Optimal (80%+)' : 'In Progress'}
            </span>
          </div>
        </div>

      </div>

      {/* 3. Bottom Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Category Breakdown & Priorities (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card className="p-6 relative overflow-hidden" hover={false}>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">
                  Focus Checklist & Priorities
                </h2>
                <p className="text-xs text-stone-400 mt-0.5">
                  High-impact actions scheduled for your workspace
                </p>
              </div>
              <Link
                to="/tasks"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                View all <ArrowUpRight size={13} />
              </Link>
            </div>

            {/* Fast Inline Add Input */}
            <form
              onSubmit={handleQuickTaskAdd}
              className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-white/10 bg-white/5 focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400 transition-all mb-4"
            >
              <div className="h-4 w-4 rounded-full border border-dashed border-stone-400 flex items-center justify-center shrink-0">
                <Plus size={11} className="text-stone-400" />
              </div>
              <input
                id="dashboard-inline-task"
                type="text"
                value={inlineTaskTitle}
                onChange={(e) => setInlineTaskTitle(e.target.value)}
                placeholder="Add a task for today... (Press Enter to save)"
                className="w-full text-xs sm:text-sm bg-transparent outline-none placeholder:text-stone-400 text-white"
              />
              {inlineTaskTitle.trim() && (
                <button
                  type="submit"
                  className="shrink-0 text-xs font-semibold bg-gradient-to-r from-indigo-500 to-violet-600 text-white px-3 py-1 rounded-lg shadow-sm"
                >
                  Save
                </button>
              )}
            </form>

            {/* Checklist items */}
            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {pending.length === 0 ? (
                <div className="py-10 text-center">
                  <div className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 mb-2">
                    <Check size={18} />
                  </div>
                  <p className="text-sm font-semibold text-white">All tasks completed</p>
                  <p className="text-xs text-stone-400 mt-0.5">You are clear for the rest of today.</p>
                </div>
              ) : (
                pending.slice(0, 6).map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between gap-3 p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 transition-all group"
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <button
                        onClick={() => setTaskStatus(task.id, 'Completed')}
                        className="h-5 w-5 rounded-full border border-stone-500 hover:border-emerald-400 hover:bg-emerald-500/20 flex items-center justify-center transition-colors shrink-0"
                        title="Mark as completed"
                      >
                        <Check size={12} className="text-transparent group-hover:text-stone-400 hover:text-emerald-400" />
                      </button>
                      <div className="min-w-0">
                        <p className="text-xs sm:text-sm font-medium text-stone-200 truncate group-hover:text-white">
                          {task.title}
                        </p>
                        {task.dueDate && (
                          <p className="text-[10px] text-stone-400 font-mono mt-0.5">
                            Due {task.dueDate} • {task.category || 'Focus'}
                          </p>
                        )}
                      </div>
                    </div>

                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${priorityPill[task.priority] || priorityPill.Medium}`}>
                      {task.priority}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Optimization Insights & Agenda (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          
          {/* Optimization Insights Card */}
          <Card className="p-6 relative overflow-hidden" hover={false}>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">
                  Optimization Insights
                </h2>
                <p className="text-xs text-stone-400 mt-0.5">
                  Automated focus and schedule diagnostics
                </p>
              </div>
              <div className="h-7 w-7 rounded-full bg-violet-500/15 text-violet-400 grid place-items-center">
                <Sparkles size={14} />
              </div>
            </div>

            <div className="space-y-3">
              {/* Tip 1 */}
              <div className="p-3 rounded-xl border border-white/10 bg-white/5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-cyan-300">⚡ Focus Acceleration</span>
                  <span className="text-[10px] font-mono text-stone-400">Real-time</span>
                </div>
                <p className="text-xs text-stone-300 leading-relaxed">
                  You have <strong className="text-white">{tasks.filter((t) => t.priority === 'High' && t.status !== 'Completed').length} high-priority</strong> tasks due today. Completing them before noon yields peak momentum.
                </p>
              </div>

              {/* Tip 2 */}
              <div className="p-3 rounded-xl border border-white/10 bg-white/5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-pink-300">🛡️ Workflow Health</span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">Optimal 80%</span>
                </div>
                <p className="text-xs text-stone-300 leading-relaxed">
                  Overall completion velocity is healthy across active categories with zero blockers logged.
                </p>
              </div>
            </div>
          </Card>

          {/* Today's Schedule Mini-Timeline */}
          <Card className="p-6 relative overflow-hidden" hover={false}>
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/10">
              <h3 className="text-sm font-bold text-white tracking-tight">
                Today's Agenda
              </h3>
              <Link to="/calendar" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5">
                Schedule <ArrowUpRight size={12} />
              </Link>
            </div>

            {todaysEvents.length === 0 ? (
              <p className="text-xs text-stone-400 py-3 text-center">No meetings or events scheduled for today.</p>
            ) : (
              <div className="space-y-2">
                {todaysEvents.slice(0, 3).map((evt) => (
                  <div
                    key={evt.id}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/5"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{evt.title}</p>
                      <p className="text-[10px] text-stone-400 font-mono mt-0.5">{evt.time}</p>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono">
                      Upcoming
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Recent Notes Preview */}
          <Card className="p-6 relative overflow-hidden" hover={false}>
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/10">
              <h3 className="text-sm font-bold text-white tracking-tight">
                Recent Notes
              </h3>
              <Link to="/notes" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5">
                Notes <ArrowUpRight size={12} />
              </Link>
            </div>

            {recentNotes.length === 0 ? (
              <p className="text-xs text-stone-400 py-3 text-center">No notes authored yet.</p>
            ) : (
              <div className="space-y-2">
                {recentNotes.slice(0, 2).map((note) => (
                  <Link
                    key={note.id}
                    to="/notes"
                    className="block p-2.5 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors"
                  >
                    <p className="text-xs font-semibold text-white truncate">{note.title}</p>
                    <p className="text-[11px] text-stone-400 line-clamp-1 mt-0.5">{note.description || 'Empty note...'}</p>
                  </Link>
                ))}
              </div>
            )}
          </Card>

        </div>

      </div>

      {/* Quick Add Task Modal */}
      <Modal open={taskModalOpen} onClose={() => setTaskModalOpen(false)} title="Create New Task">
        <form onSubmit={handleModalTaskSubmit} className="space-y-4">
          <LabeledInput
            label="Task Title"
            placeholder="e.g. Design sprint review slides"
            value={taskForm.title}
            onChange={(v) => setTaskForm((f) => ({ ...f, title: v }))}
            required
          />
          <LabeledInput
            label="Description"
            placeholder="Brief details or bullet points..."
            value={taskForm.description}
            onChange={(v) => setTaskForm((f) => ({ ...f, description: v }))}
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-stone-300 mb-1">Priority</label>
              <select
                value={taskForm.priority}
                onChange={(e) => setTaskForm((f) => ({ ...f, priority: e.target.value }))}
                className="w-full rounded-xl border border-white/15 bg-[#120e24] px-3 py-2 text-xs text-white outline-none focus:border-indigo-400"
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-300 mb-1">Due Date</label>
              <input
                type="date"
                value={taskForm.dueDate}
                onChange={(e) => setTaskForm((f) => ({ ...f, dueDate: e.target.value }))}
                className="w-full rounded-xl border border-white/15 bg-[#120e24] px-3 py-2 text-xs text-white outline-none focus:border-indigo-400"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setTaskModalOpen(false)}
              className="rounded-xl px-4 py-2 text-xs font-medium text-stone-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 px-5 py-2 text-xs font-bold text-white shadow-md shadow-indigo-500/25"
            >
              Save Task
            </button>
          </div>
        </form>
      </Modal>

    </div>
  );
}
