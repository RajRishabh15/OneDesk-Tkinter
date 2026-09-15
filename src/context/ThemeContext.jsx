import { createContext, useContext, useEffect, useState } from 'react';
import { loadData, saveData, STORAGE_KEYS } from '../utils/storage';

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return loadData(STORAGE_KEYS.THEME, 'dark');
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.body.classList.toggle('dark', theme === 'dark');
    saveData(STORAGE_KEYS.THEME, theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
