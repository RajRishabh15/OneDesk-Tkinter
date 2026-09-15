import { useMemo, useState, useRef, useEffect } from 'react';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import {
  Search,
  Bell,
  LogOut,
  User as UserIcon,
  Plus,
  CheckSquare,
  FileText,
  CalendarPlus,
  X,
  LayoutGrid,
  StickyNote,
  Calendar,
  BarChart2,
  Sliders,
  Menu
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

const navLinks = [
  { to: '/', label: 'Overview', icon: LayoutGrid, end: true },
  { to: '/tasks', label: 'Tasks', icon: CheckSquare },
  { to: '/notes', label: 'Notes', icon: StickyNote },
  { to: '/calendar', label: 'Schedule', icon: Calendar },
  { to: '/analytics', label: 'Insights', icon: BarChart2 },
  { to: '/settings', label: 'Settings', icon: Sliders },
];

export default function TopNavPill() {
  const { user, logout } = useAuth();
  const { tasks, notes, events } = useData();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const searchBoxRef = useRef(null);
  const searchInputRef = useRef(null);
  const profileRef = useRef(null);
  const notifRef = useRef(null);
  const quickAddRef = useRef(null);
  const mobileMenuRef = useRef(null);

  function handleLogout() {
    setProfileOpen(false);
    setMobileMenuOpen(false);
    logout();
    navigate('/login', { replace: true });
  }

  // Close menus on click outside
  useEffect(() => {
    function onClickAway(e) {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target)) {
        setSearchOpen(false);
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
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(e.target)) {
        setMobileMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', onClickAway);
    return () => document.removeEventListener('mousedown', onClickAway);
  }, []);

  // Keyboard shortcut Ctrl+K to open search
  useEffect(() => {
    function onKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
        setTimeout(() => searchInputRef.current?.focus(), 50);
      }
      if (e.key === 'Escape') {
        setSearchOpen(false);
        setProfileOpen(false);
        setNotifOpen(false);
        setQuickAddOpen(false);
        setMobileMenuOpen(false);
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
    .toUpperCase() || 'OD';

  return (
    <header className="fixed top-3 sm:top-4 inset-x-0 z-40 flex justify-center px-3 sm:px-4 pointer-events-none">
      <div className="pointer-events-auto relative w-full max-w-5xl rounded-2xl sm:rounded-full border border-white/10 dark:border-white/10 bg-[#0e0a1f]/80 dark:bg-[#0e0a1f]/85 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,0,0,0.45)] px-3 sm:px-4 py-2 flex items-center justify-between gap-2 sm:gap-3 transition-all">
        
        {/* Left: Brand Pill */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group">
          <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-pink-500 via-indigo-500 to-cyan-400 p-[1.5px] grid place-items-center shadow-md shadow-pink-500/20 group-hover:scale-105 transition-transform">
            <div className="h-full w-full rounded-full bg-[#0e0a1f] grid place-items-center text-[10px] font-bold text-cyan-300">
              ✦
            </div>
          </div>
          <span className="font-display text-sm font-extrabold tracking-tight text-white hidden xs:inline">
            OneDesk
          </span>
        </Link>

        {/* Center: Nav Pills with Active White Capsule & Pink Indicator Dot */}
        <nav className="hidden md:flex items-center gap-1 bg-black/40 p-1 rounded-full border border-white/10">
          {navLinks.slice(0, 5).map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `relative px-3.5 py-1.5 rounded-full text-[11px] font-extrabold tracking-wider uppercase transition-all duration-200 ${
                  isActive
                    ? 'bg-white text-stone-950 shadow-[0_2px_10px_rgba(255,255,255,0.2)]'
                    : 'text-stone-300 hover:text-white hover:bg-white/5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span>{label === 'Overview' ? 'Home' : label}</span>
                  {isActive && (
                    <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 h-1.5 w-1.5 rounded-full bg-pink-500 shadow-[0_0_8px_#ec4899]" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Right: Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
          
          {/* Search Trigger */}
          <div className="relative" ref={searchBoxRef}>
            <button
              onClick={() => {
                setSearchOpen((v) => !v);
                setTimeout(() => searchInputRef.current?.focus(), 50);
              }}
              title="Search (Ctrl+K)"
              className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 px-2.5 py-1 text-xs text-stone-300 transition-colors"
            >
              <Search size={13} />
              <span className="hidden sm:inline text-[11px] text-stone-400">Search</span>
              <kbd className="hidden sm:inline font-mono text-[9px] bg-white/10 text-stone-400 px-1.5 py-0.5 rounded">
                Ctrl+K
              </kbd>
            </button>

            {/* Search Dropdown / Popover */}
            {searchOpen && (
              <div className="absolute right-0 sm:left-1/2 sm:-translate-x-1/2 mt-2 w-80 sm:w-96 rounded-2xl border border-white/15 bg-[#120e24]/95 backdrop-blur-2xl shadow-2xl p-3 space-y-3 animate-fade-up z-50">
                <div className="relative">
                  <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
                  <input
                    ref={searchInputRef}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Type to search tasks, notes, schedule…"
                    className="w-full rounded-xl border border-white/15 bg-white/5 py-2 pl-9 pr-8 text-xs text-white outline-none placeholder:text-stone-400 focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400"
                  />
                  {query && (
                    <button
                      onClick={() => setQuery('')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-white"
                    >
                      <X size={13} />
                    </button>
                  )}
                </div>

                {query.trim() && (
                  <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                    <SearchGroup
                      label="Tasks"
                      count={results.tasks.length}
                      items={results.tasks.map((t) => t.title)}
                      onSee={() => { setSearchOpen(false); navigate('/tasks'); }}
                    />
                    <SearchGroup
                      label="Notes"
                      count={results.notes.length}
                      items={results.notes.map((n) => n.title)}
                      onSee={() => { setSearchOpen(false); navigate('/notes'); }}
                    />
                    <SearchGroup
                      label="Schedule"
                      count={results.events.length}
                      items={results.events.map((e) => e.title)}
                      onSee={() => { setSearchOpen(false); navigate('/calendar'); }}
                    />
                    {results.notes.length + results.tasks.length + results.events.length === 0 && (
                      <p className="text-xs text-stone-400 py-2 text-center">No results for "{query}".</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quick Add Pill Button */}
          <div className="relative" ref={quickAddRef}>
            <button
              onClick={() => {
                setQuickAddOpen((v) => !v);
                setProfileOpen(false);
                setNotifOpen(false);
              }}
              className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white px-3 py-1 text-xs font-semibold shadow-md shadow-indigo-500/25 transition-all"
            >
              <Plus size={13} />
              <span className="hidden sm:inline">New</span>
            </button>

            {quickAddOpen && (
              <div className="absolute right-0 mt-2 w-44 rounded-xl border border-white/15 bg-[#120e24]/95 backdrop-blur-2xl shadow-2xl p-1.5 animate-fade-up z-50">
                <button
                  onClick={() => { setQuickAddOpen(false); navigate('/tasks'); }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-stone-200 hover:bg-white/10 transition-colors"
                >
                  <CheckSquare size={14} className="text-indigo-400" />
                  Task
                </button>
                <button
                  onClick={() => { setQuickAddOpen(false); navigate('/notes'); }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-stone-200 hover:bg-white/10 transition-colors"
                >
                  <FileText size={14} className="text-emerald-400" />
                  Note
                </button>
                <button
                  onClick={() => { setQuickAddOpen(false); navigate('/calendar'); }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-stone-200 hover:bg-white/10 transition-colors"
                >
                  <CalendarPlus size={14} className="text-amber-400" />
                  Event
                </button>
              </div>
            )}
          </div>

          {/* Deadline Notifications */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => {
                setNotifOpen((v) => !v);
                setProfileOpen(false);
                setQuickAddOpen(false);
              }}
              className="relative rounded-full p-1.5 text-stone-300 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Notifications"
            >
              <Bell size={16} />
              {dueSoon.length > 0 && (
                <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-[#0e0a1f]" />
              )}
            </button>

            {notifOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-white/15 bg-[#120e24]/95 backdrop-blur-2xl shadow-2xl p-3 animate-fade-up z-50">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold text-white">Upcoming Deadlines</p>
                  {dueSoon.length > 0 && (
                    <span className="text-[10px] font-semibold bg-rose-500/20 text-rose-300 px-1.5 py-0.5 rounded border border-rose-500/30">
                      {dueSoon.length} due
                    </span>
                  )}
                </div>
                {dueSoon.length === 0 ? (
                  <p className="text-xs text-stone-400 py-2 text-center">All caught up.</p>
                ) : (
                  <ul className="space-y-1.5 max-h-56 overflow-y-auto">
                    {dueSoon.slice(0, 5).map((t) => (
                      <li
                        key={t.id}
                        className="text-xs p-1.5 rounded-lg hover:bg-white/10 cursor-pointer"
                        onClick={() => { setNotifOpen(false); navigate('/tasks'); }}
                      >
                        <span className="font-medium block text-stone-200 truncate">{t.title}</span>
                        <span className="block text-[10px] text-stone-400 font-mono">Due {t.dueDate}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Settings Link */}
          <NavLink
            to="/settings"
            title="Settings"
            className={({ isActive }) =>
              `rounded-full p-1.5 transition-colors ${
                isActive ? 'bg-white/15 text-white' : 'text-stone-300 hover:text-white hover:bg-white/10'
              }`
            }
          >
            <Sliders size={15} />
          </NavLink>

          {/* User Profile & Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => {
                setProfileOpen((v) => !v);
                setNotifOpen(false);
                setQuickAddOpen(false);
              }}
              className="flex items-center gap-1.5 rounded-full p-0.5 hover:ring-2 hover:ring-white/20 transition-all"
            >
              <div className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-violet-600 to-indigo-700 text-white text-[10px] font-bold shadow-xs">
                {initials || <UserIcon size={12} />}
              </div>
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-2xl border border-white/15 bg-[#120e24]/95 backdrop-blur-2xl shadow-2xl p-1.5 animate-fade-up z-50">
                <div className="px-3 py-2 border-b border-white/10 mb-1">
                  <p className="text-xs font-semibold text-white truncate">{user?.name || 'User'}</p>
                  <p className="text-[10px] text-stone-400 truncate font-mono">{user?.email || 'Logged in'}</p>
                </div>
                <button
                  onClick={() => { setProfileOpen(false); navigate('/settings'); }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs text-stone-200 hover:bg-white/10 transition-colors"
                >
                  <UserIcon size={13} /> Account
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <LogOut size={13} /> Log out
                </button>
              </div>
            )}
          </div>

          {/* Mobile Hamburger Toggle */}
          <div className="md:hidden relative" ref={mobileMenuRef}>
            <button
              onClick={() => setMobileMenuOpen((v) => !v)}
              className="rounded-full p-1.5 text-stone-300 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Toggle menu"
            >
              <Menu size={16} />
            </button>

            {/* Mobile Dropdown Menu */}
            {mobileMenuOpen && (
              <div className="absolute right-0 mt-2 w-52 rounded-2xl border border-white/15 bg-[#120e24]/95 backdrop-blur-2xl shadow-2xl p-2 animate-fade-up z-50">
                <div className="space-y-1">
                  {navLinks.map(({ to, label, icon: Icon, end }) => (
                    <NavLink
                      key={to}
                      to={to}
                      end={end}
                      onClick={() => setMobileMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                          isActive
                            ? 'bg-white/15 text-white font-semibold'
                            : 'text-stone-300 hover:text-white hover:bg-white/10'
                        }`
                      }
                    >
                      <Icon size={14} />
                      <span>{label}</span>
                    </NavLink>
                  ))}
                </div>
              </div>
            )}
          </div>

        </div>

      </div>
    </header>
  );
}

function SearchGroup({ label, count, items, onSee }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <p className="text-[11px] font-bold uppercase tracking-wider text-stone-400">
          {label} ({count})
        </p>
        {count > 0 && (
          <button onClick={onSee} className="text-[11px] font-semibold text-indigo-400 hover:underline">
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
              className="truncate text-xs text-stone-300 py-1 px-2 rounded-lg hover:bg-white/10 cursor-pointer"
            >
              {t}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
