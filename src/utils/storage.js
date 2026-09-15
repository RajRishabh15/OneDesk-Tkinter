// Thin wrapper around localStorage so every read/write is JSON-safe
// and failures (private browsing, quota, corrupt data) never crash the app.

const PREFIX = 'lifeos:';

export function loadData(key, fallback) {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (raw === null) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function saveData(key, value) {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function removeData(key) {
  try {
    localStorage.removeItem(PREFIX + key);
  } catch {
    /* ignore */
  }
}

export function clearAllData() {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith(PREFIX))
      .forEach((k) => localStorage.removeItem(k));
  } catch {
    /* ignore */
  }
}

export function exportBackup() {
  const backup = {};
  Object.keys(localStorage)
    .filter((k) => k.startsWith(PREFIX))
    .forEach((k) => {
      backup[k.slice(PREFIX.length)] = JSON.parse(localStorage.getItem(k));
    });
  return backup;
}

export function importBackup(backup) {
  Object.entries(backup).forEach(([key, value]) => saveData(key, value));
}

export const STORAGE_KEYS = {
  USER: 'user',
  USERS: 'users',
  NOTES: 'notes',
  TASKS: 'tasks',
  EVENTS: 'events',
  THEME: 'theme',
  SEEDED: 'seeded',
};
