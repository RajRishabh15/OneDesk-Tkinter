import { createContext, useContext, useEffect, useState } from 'react';
import { loadData, saveData, removeData, STORAGE_KEYS } from '../utils/storage';

const AuthContext = createContext(null);

export const DEMO_USER = {
  id: 'demo-user-alex',
  name: 'Alex Rivera',
  email: 'alex@lifeos.workspace',
};

function hash(str) {
  // Not real cryptography — just enough to avoid storing raw passwords in
  // plain text for this frontend-only demo.
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return String(h);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => loadData(STORAGE_KEYS.USER, null));
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    if (user) {
      saveData(STORAGE_KEYS.USER, user);
    }
  }, [user]);

  function signup({ name, email, password }) {
    setAuthError('');
    const users = loadData(STORAGE_KEYS.USERS, []);
    if (users.some((u) => u.email === email)) {
      setAuthError('An account with this email already exists.');
      return false;
    }
    const newUser = { id: crypto.randomUUID(), name, email, passwordHash: hash(password) };
    saveData(STORAGE_KEYS.USERS, [...users, newUser]);
    const publicUser = { id: newUser.id, name, email };
    setUser(publicUser);
    saveData(STORAGE_KEYS.USER, publicUser);
    return true;
  }

  function login({ email, password }) {
    setAuthError('');
    // Allow instant demo login if demo credentials entered
    if (email === DEMO_USER.email) {
      return demoLogin();
    }
    const users = loadData(STORAGE_KEYS.USERS, []);
    const match = users.find((u) => u.email === email && u.passwordHash === hash(password));
    if (!match) {
      setAuthError('Email or password is incorrect.');
      return false;
    }
    const publicUser = { id: match.id, name: match.name, email: match.email };
    setUser(publicUser);
    saveData(STORAGE_KEYS.USER, publicUser);
    return true;
  }

  function demoLogin() {
    setAuthError('');
    setUser(DEMO_USER);
    saveData(STORAGE_KEYS.USER, DEMO_USER);
    return true;
  }

  function logout() {
    setUser(null);
    removeData(STORAGE_KEYS.USER);
  }

  function updateProfile(patch) {
    setUser((prev) => {
      if (!prev) return null;
      const next = { ...prev, ...patch };
      saveData(STORAGE_KEYS.USER, next);
      const users = loadData(STORAGE_KEYS.USERS, []).map((u) =>
        u.id === next.id ? { ...u, ...patch } : u
      );
      saveData(STORAGE_KEYS.USERS, users);
      return next;
    });
  }

  return (
    <AuthContext.Provider value={{ user, authError, login, demoLogin, signup, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
