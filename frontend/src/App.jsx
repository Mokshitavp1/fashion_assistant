import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import Login from './components/Login';
import Onboarding from './components/Onboarding';
import Dashboard from './components/Dashboard';
import Wardrobe from './components/Wardrobe';
import Outfits from './components/Outfits';
import Shopping from './components/Shopping';
import Discard from './components/discard';
import Sessions from './components/Sessions';

function hasActiveAuth() {
  const accessToken = localStorage.getItem('accessToken');
  const userId = localStorage.getItem('userId');
  return Boolean(accessToken && userId);
}

function PublicOnlyRoute({ children }) {
  if (hasActiveAuth()) {
    return <Navigate to="/dashboard" replace />;
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
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/wardrobe" element={<Wardrobe />} />
        <Route path="/outfits" element={<Outfits />} />
        <Route path="/shopping" element={<Shopping />} />
        <Route path="/discard" element={<Discard />} />
        <Route path="/sessions" element={<Sessions />} />
      </Routes>
    </Router>
  );
}

export default App;