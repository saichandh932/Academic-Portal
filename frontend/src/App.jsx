import { Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import ParentDashboard from './pages/ParentDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ResetPassword from './pages/ResetPassword';
import { ProtectedRoute } from './components/AuthGuard';
import NotFound from './pages/NotFound';

function App() {
  return (
    <div className="app-container flex flex-col min-h-screen">
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Login />} />
          
          <Route 
            path="/student/:id" 
            element={
              <ProtectedRoute allowedRole="Student">
                <StudentDashboard />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/parent/:id" 
            element={
              <ProtectedRoute allowedRole="Parent">
                <ParentDashboard />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute allowedRole="Staff">
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />
          
          <Route path="/reset-password" element={<ResetPassword />} />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
