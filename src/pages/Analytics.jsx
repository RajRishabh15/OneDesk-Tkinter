import { useMemo } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import Card from '../components/Card';
import { useData } from '../context/DataContext';
import { useTheme } from '../context/ThemeContext';

const priorityColors = { High: '#dc2626', Medium: '#d97706', Low: '#16a34a' };

function lastNDays(n) {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (n - 1 - i));
    return d;
  });
}

export default function Analytics() {
  const { tasks, notes } = useData();
  const { theme } = useTheme();

  const isDark = theme === 'dark';
  const barColor = isDark ? '#e7e5e4' : '#1c1917';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(28, 25, 23, 0.06)';
  const tickColor = isDark ? '#78716c' : '#a8a29e';

  const weekly = useMemo(() => {
    const days = lastNDays(7);
    return days.map((d) => {
      const iso = d.toISOString().slice(0, 10);
      const completedThatDay = tasks.filter((t) => t.status === 'Completed' && t.dueDate === iso).length;
      return { day: d.toLocaleDateString(undefined, { weekday: 'short' }), completed: completedThatDay };
    });
  }, [tasks]);

  const byPriority = useMemo(() => {
    const groups = { High: 0, Medium: 0, Low: 0 };
    tasks.forEach((t) => { groups[t.priority] = (groups[t.priority] || 0) + 1; });
    return Object.entries(groups).map(([name, value]) => ({ name, value }));
  }, [tasks]);

  const byStatus = useMemo(() => {
    const groups = { Todo: 0, 'In Progress': 0, Completed: 0 };
    tasks.forEach((t) => { groups[t.status] = (groups[t.status] || 0) + 1; });
    return Object.entries(groups).map(([name, value]) => ({ name, value }));
  }, [tasks]);

  const completed = tasks.filter((t) => t.status === 'Completed').length;
  const productivityScore = tasks.length ? Math.round((completed / tasks.length) * 100) : 0;
  const notesThisWeek = notes.filter((n) => (Date.now() - new Date(n.createdAt)) / 86400000 <= 7).length;

  return (
    <div className="space-y-6 animate-fade-up max-w-6xl mx-auto">
      <div>
        <h1 className="font-serif text-2xl sm:text-3xl font-normal tracking-tight text-stone-900 dark:text-stone-100">
          Insights
        </h1>
        <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400 mt-1">
          Weekly cadence, priority distribution, and velocity.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Tasks completed" value={completed} sub={`out of ${tasks.length} total tasks`} />
        <Stat label="Notes authored" value={notesThisWeek} sub="in the past 7 days" />
        <Stat label="Completion rate" value={`${productivityScore}%`} sub="overall workflow progress" highlight />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5" hover={false}>
          <div className="mb-4 pb-2 border-b border-stone-100 dark:border-stone-800 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
              Weekly Activity
            </h2>
            <span className="font-mono text-[11px] text-stone-400">Past 7 days</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weekly}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: tickColor }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: tickColor }} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)' }}
                contentStyle={{
                  backgroundColor: isDark ? '#191917' : '#ffffff',
                  borderColor: isDark ? '#2e2e2a' : '#e7e5e4',
                  borderRadius: 8,
                  fontSize: 12,
                  color: isDark ? '#f5f5f4' : '#1c1917',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                }}
              />
              <Bar dataKey="completed" fill={barColor} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-5" hover={false}>
          <div className="mb-4 pb-2 border-b border-stone-100 dark:border-stone-800 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
              Tasks by Priority
            </h2>
            <span className="font-mono text-[11px] text-stone-400">{tasks.length} total</span>
          </div>
          <ResponsiveContainer width="100%" height={190}>
            <PieChart>
              <Pie data={byPriority} dataKey="value" nameKey="name" innerRadius={50} outerRadius={72} paddingAngle={4}>
                {byPriority.map((entry) => (
                  <Cell key={entry.name} fill={priorityColors[entry.name]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#191917' : '#ffffff',
                  borderColor: isDark ? '#2e2e2a' : '#e7e5e4',
                  borderRadius: 8,
                  fontSize: 12,
                  color: isDark ? '#f5f5f4' : '#1c1917',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 text-xs mt-2">
            {byPriority.map((p) => (
              <span key={p.name} className="flex items-center gap-1.5 text-stone-600 dark:text-stone-300 font-medium">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: priorityColors[p.name] }} />
                <span>{p.name}</span>
                <span className="font-mono text-stone-400 text-[11px]">({p.value})</span>
              </span>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5" hover={false}>
        <div className="mb-4 pb-2 border-b border-stone-100 dark:border-stone-800 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-stone-400">
            Pipeline Distribution
          </h2>
          <span className="font-mono text-[11px] text-stone-400">By status</span>
        </div>
        <div className="space-y-3.5">
          {byStatus.map((s) => {
            const pct = tasks.length ? Math.round((s.value / tasks.length) * 100) : 0;
            return (
              <div key={s.name}>
                <div className="mb-1.5 flex justify-between text-xs font-medium text-stone-700 dark:text-stone-300">
                  <span>{s.name}</span>
                  <span className="font-mono text-stone-400">{s.value} tasks · {pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-stone-100 dark:bg-stone-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-stone-900 dark:bg-stone-100 transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

function Stat({ label, value, sub, highlight = false }) {
  return (
    <Card className="p-5 flex flex-col justify-between" hover={false}>
      <p className="text-xs font-medium text-stone-500 dark:text-stone-400 uppercase tracking-wider">{label}</p>
      <p className={`font-serif text-3xl font-normal my-2 ${highlight ? 'text-stone-900 dark:text-stone-50' : 'text-stone-900 dark:text-stone-100'}`}>
        {value}
      </p>
      <p className="text-[11px] text-stone-400 font-mono">{sub}</p>
    </Card>
  );
}
