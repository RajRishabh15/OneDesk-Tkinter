import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AuthShell, Field } from './Login';

export default function Signup() {
  const { signup, authError } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '' });

  function handleSubmit(e) {
    e.preventDefault();
    if (signup(form)) navigate('/');
  }

  return (
    <AuthShell>
      <h1 className="font-serif text-2xl font-normal text-white">Create workspace</h1>
      <p className="mt-1 text-xs text-stone-400">Set up your personal OneDesk workspace.</p>

      <form onSubmit={handleSubmit} className="mt-5 space-y-3.5">
        <Field
          icon={User}
          type="text"
          placeholder="Full name"
          required
          value={form.name}
          onChange={(v) => setForm((f) => ({ ...f, name: v }))}
        />
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
          placeholder="Choose password"
          required
          minLength={4}
          value={form.password}
          onChange={(v) => setForm((f) => ({ ...f, password: v }))}
        />

        {authError && <p className="text-xs font-medium text-rose-400">{authError}</p>}

        <button
          type="submit"
          className="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white py-2.5 text-xs font-semibold transition-all shadow-md shadow-indigo-500/25"
        >
          Create account
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-stone-400">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-indigo-400 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
