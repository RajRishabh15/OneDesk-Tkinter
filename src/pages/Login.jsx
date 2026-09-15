import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GhostFibers from '../components/GhostFibers';

export default function Login() {
  const { login, demoLogin, authError } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });

  function handleSubmit(e) {
    e.preventDefault();
    if (login(form)) navigate('/');
  }

  function handleDemo() {
    if (demoLogin()) navigate('/');
  }

  return (
    <AuthShell>
      <h1 className="font-serif text-2xl font-normal text-white">Welcome back</h1>
      <p className="mt-1 text-xs text-stone-400">Sign in to your OneDesk workspace.</p>

      {/* Quick Demo Login CTA */}
      <div className="mt-5 p-3 rounded-xl border border-white/10 bg-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-amber-400" />
            <span className="text-xs font-semibold text-stone-200">Demo Account</span>
          </div>
          <button
            type="button"
            onClick={handleDemo}
            className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 hover:underline"
          >
            Instant Sign-in <ArrowRight size={12} />
          </button>
        </div>
      </div>

      <div className="relative my-4 flex items-center justify-center">
        <div className="w-full border-t border-white/10" />
        <span className="absolute bg-[#120e24] px-2 text-[10px] uppercase tracking-wider text-stone-400">
          or with email
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5">
        <Field
          icon={Mail}
          type="email"
          placeholder="Email address"
          required
          value={form.email}
          onChange={(v) => setForm((f) => ({ ...f, email: v }))}
        />
        <Field
          icon={Lock}
          type="password"
          placeholder="Password"
          required
          value={form.password}
          onChange={(v) => setForm((f) => ({ ...f, password: v }))}
        />

        {authError && <p className="text-xs font-medium text-rose-400">{authError}</p>}

        <button
          type="submit"
          className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white py-2.5 text-xs font-semibold transition-all shadow-md shadow-indigo-500/25"
        >
          Sign in
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-stone-400">
        Need a new workspace?{' '}
        <Link to="/signup" className="font-semibold text-indigo-400 hover:underline">
          Create account
        </Link>
      </p>
    </AuthShell>
  );
}

export function AuthShell({ children }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#090715] px-4 py-8 overflow-hidden text-stone-100">
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" style={{ width: '100vw', height: '100vh' }}>
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <GhostFibers
            lineColor="#140E35"
            glowColor="#3437A0"
            speed={0.2}
            scale={2}
            rotation={0}
            rotationSpeed={0.25}
            layers={4}
            waveAmplitude={0.015}
            waveFrequency={3}
            waveSpeed={0.15}
            layerSpeed={0.08}
            twist={0.1}
            twistFrequency={5}
            twistSpeed={1.2}
            lineFrequency={5}
            lineSpacing={2}
            lineSharpness={16}
            glowFalloff={10}
            glowIntensity={1.6}
            brightness={2}
            blueBoost={1.25}
            vignette={0.8}
            grain={0.05}
            dpr={1}
            lightMode={false}
            fps={60}
            paused={false}
          />
        </div>
        <div className="absolute inset-0 bg-[#090715]/60 backdrop-blur-[0.5px]" />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        <div className="mb-6 flex items-center justify-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white font-mono text-sm font-bold shadow-md shadow-indigo-500/30">
            OD
          </div>
          <span className="font-display text-xl font-bold tracking-tight text-white">
            OneDesk
          </span>
        </div>
        <div className="rounded-2xl border border-white/10 bg-[#120e24]/85 backdrop-blur-xl p-7 shadow-2xl animate-fade-up">
          {children}
        </div>
      </div>
    </div>
  );
}

export function Field({ icon: Icon, value, onChange, ...rest }) {
  return (
    <div className="relative">
      {Icon && (
        <Icon size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
      )}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-900/50 py-2 text-xs text-stone-900 dark:text-stone-100 outline-none transition-all placeholder:text-stone-400 focus:border-stone-400 dark:focus:border-stone-600 focus:ring-1 focus:ring-stone-400 ${
          Icon ? 'pl-8.5 pr-3' : 'px-3'
        }`}
        {...rest}
      />
    </div>
  );
}
