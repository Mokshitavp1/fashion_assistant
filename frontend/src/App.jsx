import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import Login from './components/Login';
import Onboarding from './components/Onboarding';
import Dashboard from './components/Dashboard';
import Wardrobe from './components/Wardrobe';
import Outfits from './components/outfits';
import Shopping from './components/shopping';
import Discard from './components/discard';
import Sessions from './components/Sessions';
import { hasActiveAuth } from './services/api';

function PublicOnlyRoute({ children }) {
  if (hasActiveAuth()) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

function RequireAuth({ children }) {
  if (!hasActiveAuth()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
        <Route path="/onboarding" element={<PublicOnlyRoute><Onboarding /></PublicOnlyRoute>} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/wardrobe" element={<RequireAuth><Wardrobe /></RequireAuth>} />
        <Route path="/outfits" element={<RequireAuth><Outfits /></RequireAuth>} />
        <Route path="/shopping" element={<RequireAuth><Shopping /></RequireAuth>} />
        <Route path="/discard" element={<RequireAuth><Discard /></RequireAuth>} />
        <Route path="/sessions" element={<RequireAuth><Sessions /></RequireAuth>} />
      </Routes>
    </Router>
  );
}

export default App;
