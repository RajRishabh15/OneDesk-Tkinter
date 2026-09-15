import { createContext, useContext, useEffect, useState } from 'react';
import { loadData, saveData, STORAGE_KEYS } from '../utils/storage';
import { makeSampleNotes, makeSampleTasks, makeSampleEvents } from '../utils/sampleData';

const DataContext = createContext(null);

export function DataProvider({ children }) {
  const [notes, setNotes] = useState(() => loadData(STORAGE_KEYS.NOTES, null));
  const [tasks, setTasks] = useState(() => loadData(STORAGE_KEYS.TASKS, null));
  const [events, setEvents] = useState(() => loadData(STORAGE_KEYS.EVENTS, null));

  // Seed believable sample data on a brand-new install only.
  useEffect(() => {
    if (notes === null) setNotes(makeSampleNotes());
    if (tasks === null) setTasks(makeSampleTasks());
    if (events === null) setEvents(makeSampleEvents());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (notes !== null) saveData(STORAGE_KEYS.NOTES, notes);
  }, [notes]);
  useEffect(() => {
    if (tasks !== null) saveData(STORAGE_KEYS.TASKS, tasks);
  }, [tasks]);
  useEffect(() => {
    if (events !== null) saveData(STORAGE_KEYS.EVENTS, events);
  }, [events]);

  // ---- Notes ----
  function addNote(note) {
    setNotes((prev) => [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), pinned: false, ...note }, ...(prev || [])]);
  }
  function updateNote(id, patch) {
    setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, ...patch } : n)));
  }
  function deleteNote(id) {
    setNotes((prev) => prev.filter((n) => n.id !== id));
  }
  function togglePinNote(id) {
    setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, pinned: !n.pinned } : n)));
  }

  // ---- Tasks ----
  function addTask(task) {
    setTasks((prev) => [{ id: crypto.randomUUID(), status: 'Todo', ...task }, ...(prev || [])]);
  }
  function updateTask(id, patch) {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)));
  }
  function deleteTask(id) {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }
  function setTaskStatus(id, status) {
    updateTask(id, { status });
  }

  // ---- Events ----
  function addEvent(event) {
    setEvents((prev) => [{ id: crypto.randomUUID(), reminder: false, ...event }, ...(prev || [])]);
  }
  function updateEvent(id, patch) {
    setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  }
  function deleteEvent(id) {
    setEvents((prev) => prev.filter((e) => e.id !== id));
  }

  function clearAll() {
    setNotes([]);
    setTasks([]);
    setEvents([]);
  }

  const value = {
    notes: notes || [],
    tasks: tasks || [],
    events: events || [],
    addNote, updateNote, deleteNote, togglePinNote,
    addTask, updateTask, deleteTask, setTaskStatus,
    addEvent, updateEvent, deleteEvent,
    clearAll,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error('useData must be used within DataProvider');
  return ctx;
}
