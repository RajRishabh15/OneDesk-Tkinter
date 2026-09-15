import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Moon, Sun, Bell, Download, Upload, Trash2, User, LogOut } from 'lucide-react';
import Card from '../components/Card';
import { LabeledInput } from './Notes';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import { exportBackup, importBackup } from '../utils/storage';

export default function Settings() {
  const { theme, toggleTheme } = useTheme();
  const { user, updateProfile, logout } = useAuth();
  const { clearAll } = useData();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name || '');
  const [notifOn, setNotifOn] = useState(true);
  const [savedTick, setSavedTick] = useState(false);
  const fileRef = useRef(null);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  function saveProfile(e) {
    e.preventDefault();
    updateProfile({ name });
    setSavedTick(true);
    setTimeout(() => setSavedTick(false), 1800);
  }

  function handleExport() {
    const blob = new Blob([JSON.stringify(exportBackup(), null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'onedesk-backup.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleImport(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        importBackup(JSON.parse(reader.result));
        window.location.reload();
      } catch {
        alert('That file could not be read as a OneDesk backup.');
      }
    };
    reader.readAsText(file);
  }

  function handleClearData() {
    if (confirm('This clears all notes, tasks, and events. This cannot be undone. Continue?')) {
      clearAll();
    }
  }

  return (
    <div className="max-w-2xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-serif text-2xl sm:text-3xl font-normal tracking-tight text-stone-900 dark:text-stone-100">
          Preferences
        </h1>
        <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400 mt-1">
          Manage your identity, theme appearance, and workspace data.
        </p>
      </div>

      <Card className="p-5" hover={false}>
        <div className="mb-4 pb-2.5 border-b border-stone-100 dark:border-stone-800 flex items-center gap-2">
          <User size={15} className="text-stone-500 dark:text-stone-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
            Profile
          </h2>
        </div>
        <form onSubmit={saveProfile} className="space-y-4">
          <LabeledInput label="Full name" value={name} onChange={setName} />
          <LabeledInput label="Email" value={user?.email || ''} disabled className="opacity-60 cursor-not-allowed" />
          <div className="flex items-center gap-3 pt-1">
            <button
              type="submit"
              className="rounded-lg bg-stone-900 hover:bg-stone-800 text-stone-100 dark:bg-stone-100 dark:hover:bg-stone-200 dark:text-stone-900 px-4 py-2 text-xs font-medium transition-colors"
            >
              Save changes
            </button>
            {savedTick && <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">✓ Saved</span>}
          </div>
        </form>

        <div className="flex items-center justify-between pt-4 mt-4 border-t border-stone-100 dark:border-stone-800/60">
          <div>
            <p className="text-xs font-medium text-stone-800 dark:text-stone-200">Account Session</p>
            <p className="text-[11px] text-stone-500">Sign out of this browser session.</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-lg border border-stone-200/80 dark:border-stone-800 bg-stone-100/70 dark:bg-stone-900 px-3 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-300 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
          >
            <LogOut size={13} /> Log out
          </button>
        </div>
      </Card>

      <Card className="p-5" hover={false}>
        <div className="mb-4 pb-2.5 border-b border-stone-100 dark:border-stone-800">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
            Appearance
          </h2>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-stone-800 dark:text-stone-200">Interface Theme</p>
            <p className="text-xs text-stone-500 mt-0.5">Toggle between warm stone daylight and carbon graphite dark mode.</p>
          </div>
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 rounded-lg border border-stone-200/80 dark:border-stone-800 bg-stone-100/70 dark:bg-stone-900 px-3 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-200/70 dark:hover:bg-stone-800 transition-colors"
          >
            {theme === 'dark' ? <Moon size={14} /> : <Sun size={14} />}
            {theme === 'dark' ? 'Dark' : 'Light'}
          </button>
        </div>
      </Card>

      <Card className="p-5" hover={false}>
        <div className="mb-4 pb-2.5 border-b border-stone-100 dark:border-stone-800 flex items-center gap-2">
          <Bell size={15} className="text-stone-500 dark:text-stone-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
            Notifications & Signals
          </h2>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-stone-800 dark:text-stone-200">Due Task Badges</p>
            <p className="text-xs text-stone-500 mt-0.5">Show active badges in navigation for items scheduled for today.</p>
          </div>
          <button
            onClick={() => setNotifOn((v) => !v)}
            aria-label="Toggle notifications"
            className={`h-5 w-9 rounded-full transition-colors relative ${notifOn ? 'bg-stone-900 dark:bg-stone-100' : 'bg-stone-200 dark:bg-stone-700'}`}
          >
            <span
              className={`block h-4 w-4 rounded-full shadow-xs transition-transform absolute top-0.5 ${
                notifOn
                  ? 'translate-x-4.5 bg-white dark:bg-stone-900'
                  : 'translate-x-0.5 bg-white dark:bg-stone-400'
              }`}
            />
          </button>
        </div>
      </Card>

      <Card className="p-5" hover={false}>
        <div className="mb-4 pb-2.5 border-b border-stone-100 dark:border-stone-800">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
            Data Portability
          </h2>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-stone-800 dark:text-stone-200">Export Archive</p>
              <p className="text-xs text-stone-500 mt-0.5">Download tasks, notes, and schedules in standard JSON.</p>
            </div>
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 rounded-lg border border-stone-200/80 dark:border-stone-800 bg-stone-100/70 dark:bg-stone-900 px-3 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-200/70 dark:hover:bg-stone-800 transition-colors"
            >
              <Download size={13} /> Export JSON
            </button>
          </div>

          <div className="flex items-center justify-between border-t border-stone-100 dark:border-stone-800/60 pt-3">
            <div>
              <p className="text-sm font-medium text-stone-800 dark:text-stone-200">Import Archive</p>
              <p className="text-xs text-stone-500 mt-0.5">Restore tasks and notes from a previously exported file.</p>
            </div>
            <button
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-1.5 rounded-lg border border-stone-200/80 dark:border-stone-800 bg-stone-100/70 dark:bg-stone-900 px-3 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-200/70 dark:hover:bg-stone-800 transition-colors"
            >
              <Upload size={13} /> Import JSON
            </button>
            <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={handleImport} />
          </div>

          <div className="flex items-center justify-between border-t border-stone-100 dark:border-stone-800/60 pt-3">
            <div>
              <p className="text-sm font-medium text-rose-600 dark:text-rose-400">Clear Workspace</p>
              <p className="text-xs text-stone-500 mt-0.5">Permanently purge all stored tasks, notes, and calendar events.</p>
            </div>
            <button
              onClick={handleClearData}
              className="flex items-center gap-1.5 rounded-lg border border-rose-200 dark:border-rose-900/40 bg-rose-50/60 dark:bg-rose-950/30 px-3 py-1.5 text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/40 transition-colors"
            >
              <Trash2 size={13} /> Clear
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}
