// Generates believable starter content so a fresh account isn't an empty void.
// All dates are relative to "today" so the demo never looks stale.

function isoDate(offsetDays) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

export function makeSampleNotes() {
  return [
    {
      id: crypto.randomUUID(),
      title: 'Machine Learning Notes',
      description: 'Topics:\n- Regression\n- Neural Networks\n- Gradient Descent\n\nRevisit backprop derivation before the quiz.',
      category: 'College',
      tags: ['AI', 'College'],
      color: 'violet',
      pinned: true,
      createdAt: new Date().toISOString(),
    },
    {
      id: crypto.randomUUID(),
      title: 'Q3 Product Roadmap',
      description: '## Themes\n- Onboarding revamp\n- Mobile performance\n- Analytics v2\n\nSync with design on Thursday.',
      category: 'Work',
      tags: ['Work', 'Planning'],
      color: 'cyan',
      pinned: false,
      createdAt: isoDate(-1),
    },
    {
      id: crypto.randomUUID(),
      title: 'Book List — Autumn',
      description: '- Deep Work\n- The Pragmatic Programmer\n- Atomic Habits (reread)',
      category: 'Personal',
      tags: ['Reading'],
      color: 'green',
      pinned: false,
      createdAt: isoDate(-3),
    },
  ];
}

export function makeSampleTasks() {
  return [
    {
      id: crypto.randomUUID(),
      title: 'Complete OS Assignment',
      description: 'Finish the scheduling algorithm section and write test cases.',
      priority: 'High',
      dueDate: isoDate(1),
      category: 'College',
      status: 'Todo',
    },
    {
      id: crypto.randomUUID(),
      title: 'Project Meeting Prep',
      description: 'Prepare slides summarizing sprint progress.',
      priority: 'Medium',
      dueDate: isoDate(0),
      category: 'Work',
      status: 'In Progress',
    },
    {
      id: crypto.randomUUID(),
      title: 'Grocery Run',
      description: 'Milk, eggs, coffee, vegetables.',
      priority: 'Low',
      dueDate: isoDate(0),
      category: 'Personal',
      status: 'Todo',
    },
    {
      id: crypto.randomUUID(),
      title: 'Review PR #482',
      description: 'Check the new auth middleware changes.',
      priority: 'Medium',
      dueDate: isoDate(-1),
      category: 'Work',
      status: 'Completed',
    },
    {
      id: crypto.randomUUID(),
      title: 'Read Chapter 4 — Deep Work',
      description: '',
      priority: 'Low',
      dueDate: isoDate(2),
      category: 'Personal',
      status: 'Completed',
    },
  ];
}

export function makeSampleEvents() {
  return [
    {
      id: crypto.randomUUID(),
      title: 'OS Lab',
      date: isoDate(0),
      time: '09:00',
      description: 'Bring lab notebook and pendrive.',
      reminder: true,
    },
    {
      id: crypto.randomUUID(),
      title: 'Project Meeting',
      date: isoDate(0),
      time: '14:00',
      description: 'Sprint review with the team.',
      reminder: true,
    },
    {
      id: crypto.randomUUID(),
      title: 'Dentist Appointment',
      date: isoDate(2),
      time: '11:30',
      description: '',
      reminder: false,
    },
    {
      id: crypto.randomUUID(),
      title: 'Design Sync',
      date: isoDate(4),
      time: '16:00',
      description: 'Discuss onboarding revamp mockups.',
      reminder: true,
    },
  ];
}
