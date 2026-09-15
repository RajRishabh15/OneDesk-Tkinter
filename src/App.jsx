import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { DataProvider } from './context/DataContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Notes from './pages/Notes';
import Tasks from './pages/Tasks';
import CalendarPage from './pages/Calendar';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <DataProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<Dashboard />} />
                <Route path="/notes" element={<Notes />} />
                <Route path="/tasks" element={<Tasks />} />
                <Route path="/calendar" element={<CalendarPage />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </DataProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
