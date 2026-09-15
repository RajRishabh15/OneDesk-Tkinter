import { useMemo, useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, Menu, LogOut, User as UserIcon, Plus, CheckSquare, FileText, CalendarPlus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  const { notes, tasks, events } = useData();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const boxRef = useRef(null);
  const profileRef = useRef(null);
  const notifRef = useRef(null);
  const quickAddRef = useRef(null);
  const inputRef = useRef(null);

  function handleLogout() {
    setProfileOpen(false);
    logout();
    navigate('/login', { replace: true });
  }

  useEffect(() => {
    function onClickAway(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) {
        setShowResults(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
      if (quickAddRef.current && !quickAddRef.current.contains(e.target)) {
        setQuickAddOpen(false);
      }
    }
    document.addEventListener('mousedown', onClickAway);
    return () => document.removeEventListener('mousedown', onClickAway);
  }, []);

  // Keyboard shortcut Ctrl+K or / to focus search
  useEffect(() => {
    function onKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setShowResults(true);
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const results = useMemo(() => {
    if (!query.trim()) return { notes: [], tasks: [], events: [] };
    const q = query.toLowerCase();
    return {
      notes: notes.filter((n) => n.title.toLowerCase().includes(q) || n.description?.toLowerCase().includes(q)),
      tasks: tasks.filter((t) => t.title.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q)),
      events: events.filter((e) => e.title.toLowerCase().includes(q) || e.description?.toLowerCase().includes(q)),
    };
  }, [query, notes, tasks, events]);

  const dueSoon = tasks.filter(
    (t) => t.status !== 'Completed' && t.dueDate && new Date(t.dueDate) <= new Date(Date.now() + 86400000)
  );

  const initials = user?.name
    ?.split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-stone-200/80 dark:border-stone-800/80 bg-[#fafaf9]/90 dark:bg-[#121211]/90 backdrop-blur-md px-4 md:px-6 py-2.5">
      <div className="flex items-center gap-3 flex-1 max-w-lg" ref={boxRef}>
        <button className="md:hidden text-stone-500 hover:text-stone-800 dark:hover:text-white" onClick={onMenuClick} aria-label="Open menu">
          <Menu size={18} />
        </button>

        <div className="relative flex-1">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowResults(true);
            }}
            onFocus={() => setShowResults(true)}
            placeholder="Search anything… (Ctrl+K)"
            className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1c1c1a] py-1.5 pl-8 pr-8 text-xs outline-none transition-all placeholder:text-stone-400 focus:border-stone-400 dark:focus:border-stone-600 focus:ring-1 focus:ring-stone-400"
          />
          {query && (
            <button
              onClick={() => { setQuery(''); setShowResults(false); }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
            >
              <X size={13} />
            </button>
          )}

          {showResults && query.trim() && (
            <div className="absolute mt-1.5 w-full rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1c1c1a] shadow-xl p-3 space-y-3 animate-fade-up z-50">
              <SearchGroup
                label="Tasks"
                count={results.tasks.length}
                items={results.tasks.map((t) => t.title)}
                onSee={() => { setShowResults(false); navigate('/tasks'); }}
              />
              <SearchGroup
                label="Notes"
                count={results.notes.length}
                items={results.notes.map((n) => n.title)}
                onSee={() => { setShowResults(false); navigate('/notes'); }}
              />
              <SearchGroup
                label="Schedule"
                count={results.events.length}
                items={results.events.map((e) => e.title)}
                onSee={() => { setShowResults(false); navigate('/calendar'); }}
              />
              {results.notes.length + results.tasks.length + results.events.length === 0 && (
                <p className="text-xs text-stone-400 py-1">No matches for "{query}".</p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* Quick Add Button */}
        <div className="relative" ref={quickAddRef}>
          <button
            onClick={() => {
              setQuickAddOpen((v) => !v);
              setNotifOpen(false);
              setProfileOpen(false);
            }}
            className="flex items-center gap-1.5 rounded-lg bg-stone-900 hover:bg-stone-800 dark:bg-stone-100 dark:hover:bg-white dark:text-stone-900 text-stone-100 px-3 py-1.5 text-xs font-semibold shadow-xs transition-colors"
          >
            <Plus size={13} />
            <span>New</span>
          </button>

          {quickAddOpen && (
            <div className="absolute right-0 mt-2 w-40 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1c1c1a] shadow-xl p-1.5 animate-fade-up z-50">
              <button
                onClick={() => { setQuickAddOpen(false); navigate('/tasks'); }}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
              >
                <CheckSquare size={14} className="text-stone-500" />
                Task
              </button>
              <button
                onClick={() => { setQuickAddOpen(false); navigate('/notes'); }}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
              >
                <FileText size={14} className="text-stone-500" />
                Note
              </button>
              <button
                onClick={() => { setQuickAddOpen(false); navigate('/calendar'); }}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
              >
                <CalendarPlus size={14} className="text-stone-500" />
                Event
              </button>
            </div>
          )}
        </div>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => {
              setNotifOpen((v) => !v);
              setProfileOpen(false);
              setQuickAddOpen(false);
            }}
            className="relative rounded-lg p-1.5 text-stone-500 hover:text-stone-800 hover:bg-stone-100 dark:text-stone-400 dark:hover:text-stone-100 dark:hover:bg-stone-800 transition-colors"
            aria-label="Notifications"
          >
            <Bell size={17} />
            {dueSoon.length > 0 && (
              <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-rose-600 ring-2 ring-white dark:ring-stone-900" />
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1c1c1a] shadow-xl p-3 animate-fade-up z-50">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-bold text-stone-900 dark:text-white">Deadlines</p>
                {dueSoon.length > 0 && (
                  <span className="text-[10px] font-semibold bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 px-1.5 py-0.5 rounded border border-rose-200/50 dark:border-rose-900/30">
                    {dueSoon.length} due
                  </span>
                )}
              </div>
              {dueSoon.length === 0 ? (
                <p className="text-xs text-stone-400 py-2 text-center">All caught up.</p>
              ) : (
                <ul className="space-y-1.5 max-h-56 overflow-y-auto">
                  {dueSoon.slice(0, 5).map((t) => (
                    <li key={t.id} className="text-xs p-1.5 rounded-lg hover:bg-stone-50 dark:hover:bg-stone-800/50 cursor-pointer" onClick={() => { setNotifOpen(false); navigate('/tasks'); }}>
                      <span className="font-medium block text-stone-800 dark:text-stone-200 truncate">{t.title}</span>
                      <span className="block text-[10px] text-stone-400 font-mono">Due {t.dueDate}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => {
              setProfileOpen((v) => !v);
              setNotifOpen(false);
              setQuickAddOpen(false);
            }}
            className="flex items-center gap-2 rounded-lg p-1 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          >
            <div className="grid h-6 w-6 place-items-center rounded-md bg-stone-200 dark:bg-stone-800 text-stone-700 dark:text-stone-300 text-[11px] font-bold">
              {initials || <UserIcon size={13} />}
            </div>
            <span className="hidden md:block text-xs font-medium text-stone-700 dark:text-stone-300">{user?.name?.split(' ')[0]}</span>
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-44 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1c1c1a] shadow-xl p-1 animate-fade-up z-50">
              <div className="px-2.5 py-1.5 border-b border-stone-100 dark:border-stone-800 mb-1">
                <p className="text-xs font-semibold text-stone-900 dark:text-white truncate">{user?.name}</p>
                <p className="text-[10px] text-stone-400 truncate font-mono">{user?.email}</p>
              </div>
              <button
                onClick={() => { setProfileOpen(false); navigate('/settings'); }}
                className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
              >
                <UserIcon size={13} /> Account
              </button>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
              >
                <LogOut size={13} /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function SearchGroup({ label, count, items, onSee }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          {label} ({count})
        </p>
        {count > 0 && (
          <button onClick={onSee} className="text-[11px] font-semibold text-stone-900 dark:text-stone-100 hover:underline">
            View all
          </button>
        )}
      </div>
      {count > 0 && (
        <ul className="space-y-1">
          {items.slice(0, 3).map((t, i) => (
            <li
              key={i}
              onClick={onSee}
              className="truncate text-xs text-slate-700 dark:text-slate-300 py-1 px-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            >
              {t}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
