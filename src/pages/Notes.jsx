import { useMemo, useState } from 'react';
import { Plus, Search, StickyNote, Download, X } from 'lucide-react';
import Modal from '../components/Modal';
import NoteCard from '../components/NoteCard';
import EmptyState from '../components/EmptyState';
import { useData } from '../context/DataContext';

const colors = ['violet', 'cyan', 'green', 'amber', 'rose'];
const emptyForm = { title: '', description: '', category: '', tags: '', color: 'violet' };

export default function Notes() {
  const { notes, addNote, updateNote, deleteNote, togglePinNote } = useData();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const categories = ['All', ...new Set(notes.map((n) => n.category).filter(Boolean))];

  const filtered = useMemo(() => {
    let list = notes;
    if (category !== 'All') list = list.filter((n) => n.category === category);
    if (query.trim()) {
      const q = query.toLowerCase();
      list = list.filter((n) => n.title.toLowerCase().includes(q) || n.description?.toLowerCase().includes(q) || n.tags?.some((t) => t.toLowerCase().includes(q)));
    }
    return [...list].sort((a, b) => (b.pinned - a.pinned) || new Date(b.createdAt) - new Date(a.createdAt));
  }, [notes, query, category]);

  function openNew() {
    setEditing(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(note) {
    setEditing(note);
    setForm({ ...note, tags: note.tags?.join(', ') || '' });
    setModalOpen(true);
  }

  function handleSubmit(e) {
    e.preventDefault();
    const payload = {
      title: form.title.trim(),
      description: form.description,
      category: form.category.trim() || 'General',
      tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
      color: form.color,
    };
    if (editing) updateNote(editing.id, payload);
    else addNote(payload);
    setModalOpen(false);
  }

  function exportNote(note) {
    const text = `${note.title}\n\n${note.description}\n\nTags: ${note.tags?.join(', ')}\nCategory: ${note.category}\nCreated: ${new Date(note.createdAt).toLocaleString()}`;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${note.title.replace(/\s+/g, '_') || 'note'}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-5 animate-fade-up max-w-6xl mx-auto pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-stone-200/80 dark:border-stone-800/80 pb-4">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-100">Notes</h1>
          <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">{notes.length} notes captured</p>
        </div>
        <button
          onClick={openNew}
          className="flex items-center gap-1.5 rounded-lg bg-stone-900 hover:bg-stone-800 dark:bg-stone-100 dark:hover:bg-white dark:text-stone-900 text-stone-100 px-3.5 py-1.5 text-xs font-semibold shadow-xs transition-colors"
        >
          <Plus size={13} /> New note
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={13} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search notes or tags…"
            className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-white dark:bg-[#1c1c1a] py-1.5 pl-8 pr-7 text-xs outline-none transition-all placeholder:text-stone-400 focus:border-stone-400 dark:focus:border-stone-600 focus:ring-1 focus:ring-stone-400"
          />
          {query && (
            <button onClick={() => setQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600">
              <X size={13} />
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={[
                'rounded-lg px-2.5 py-1 text-xs font-medium transition-colors',
                category === c
                  ? 'bg-stone-900 text-stone-100 dark:bg-stone-100 dark:text-stone-900 shadow-xs'
                  : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-400 hover:bg-stone-100/60 dark:hover:bg-stone-800/60',
              ].join(' ')}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={StickyNote}
          title={notes.length === 0 ? 'No notes yet' : 'No matching notes'}
          description={notes.length === 0 ? 'Capture your thoughts, plans, and ideas in one place.' : 'Try a different search term or category.'}
          action={notes.length === 0 && (
            <button onClick={openNew} className="mt-2 rounded-lg bg-stone-900 text-stone-100 dark:bg-stone-100 dark:text-stone-900 px-3.5 py-1.5 text-xs font-semibold">
              Create your first note
            </button>
          )}
        />
      ) : (
        <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((note) => (
            <div key={note.id} className="relative group">
              <NoteCard note={note} onEdit={openEdit} onDelete={deleteNote} onTogglePin={togglePinNote} />
              <button
                onClick={() => exportNote(note)}
                aria-label="Export note as text file"
                title="Export as .txt"
                className="absolute right-3.5 bottom-3.5 opacity-0 group-hover:opacity-100 rounded-md bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 p-1 text-stone-400 hover:text-stone-900 dark:hover:text-stone-100 shadow-xs transition-opacity"
              >
                <Download size={11} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Note Modal */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit note' : 'New note'} wide>
        <form onSubmit={handleSubmit} className="space-y-4">
          <LabeledInput label="Title" required value={form.title} onChange={(v) => setForm((f) => ({ ...f, title: v }))} placeholder="Note title..." />
          <div>
            <label className="mb-1 block text-xs font-semibold text-stone-600 dark:text-stone-300">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={7}
              placeholder="Jot down notes, links, thoughts..."
              className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-900 p-3 text-xs sm:text-sm font-sans outline-none leading-relaxed transition-all placeholder:text-stone-400 focus:bg-white dark:focus:bg-stone-900 focus:border-stone-400"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <LabeledInput label="Category" placeholder="e.g. Work, Ideas" value={form.category} onChange={(v) => setForm((f) => ({ ...f, category: v }))} />
            <LabeledInput label="Tags (comma separated)" placeholder="roadmap, design" value={form.tags} onChange={(v) => setForm((f) => ({ ...f, tags: v }))} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-stone-600 dark:text-stone-300">Accent strip</label>
            <div className="flex gap-2">
              {colors.map((c) => (
                <button
                  type="button"
                  key={c}
                  onClick={() => setForm((f) => ({ ...f, color: c }))}
                  className={`h-5 w-5 rounded-full border-2 transition-transform ${form.color === c ? 'border-stone-900 dark:border-stone-100 scale-110 shadow-xs' : 'border-transparent hover:scale-105'}`}
                  style={{ background: { violet: '#292524', cyan: '#0284c7', green: '#059669', amber: '#d97706', rose: '#e11d48' }[c] }}
                  aria-label={c}
                />
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-3 border-t border-stone-100 dark:border-stone-800">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="rounded-lg border border-stone-200 dark:border-stone-800 px-3 py-1.5 text-xs font-medium text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-stone-900 hover:bg-stone-800 dark:bg-stone-100 dark:hover:bg-white dark:text-stone-900 text-stone-100 px-3.5 py-1.5 text-xs font-semibold shadow-xs transition-colors"
            >
              {editing ? 'Save changes' : 'Add note'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function LabeledInput({ label, value, onChange, placeholder = '', ...rest }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-semibold text-stone-600 dark:text-stone-300">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-stone-200 dark:border-stone-800 bg-stone-50 dark:bg-stone-900 px-2.5 py-1.5 text-xs outline-none transition-all placeholder:text-stone-400 focus:bg-white dark:focus:bg-stone-900 focus:border-stone-400"
        {...rest}
      />
    </div>
  );
}

export { LabeledInput };
