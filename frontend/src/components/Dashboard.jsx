import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser, logoutUser } from '../services/api';
import { User, Shirt, Sparkles, ShoppingBag, LogOut, Shield } from 'lucide-react';
import { sharedCSS } from './sharedStyles';

function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const userId = localStorage.getItem('userId');

  const fetchUser = useCallback(async () => {
    try {
      const response = await getUser(userId);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      navigate('/onboarding');
    } finally {
      setLoading(false);
    }
  }, [navigate, userId]);

  useEffect(() => {
    if (!userId) { navigate('/onboarding'); return; }
    fetchUser();
  }, [fetchUser, userId, navigate]);

  const handleLogout = async () => {
    await logoutUser();
    navigate('/');
  };

  if (loading || !user) {
    return (
      <>
        <style>{sharedCSS}</style>
        <div className="loader-wrap">
          <div className="loader-ring" />
          <p className="loader-text">Dressing up your dashboard…</p>
        </div>
      </>
    );
  }

  const stats = [
    { label: 'Body Shape', value: user?.body_shape || '—', cls: 'stat-accent' },
    { label: 'Undertone', value: user?.undertone || '—', cls: 'stat-accent' },
    { label: 'Height', value: user?.height ? `${user.height} cm` : '—', cls: '' },
    { label: 'BMI', value: user?.bmi ? user.bmi.toFixed(1) : '—', cls: '' },
  ];

  const actions = [
    { icon: <Shirt size={22} />, title: 'My Wardrobe', desc: 'View and manage your clothing items', path: '/wardrobe' },
    { icon: <Sparkles size={22} />, title: 'Outfit Ideas', desc: 'ML-powered outfit recommendations just for you', path: '/outfits' },
    { icon: <ShoppingBag size={22} />, title: 'Shopping Assistant', desc: 'Check if a new item matches your wardrobe', path: '/shopping' },
    { icon: <Shield size={22} />, title: 'Security Sessions', desc: 'Review and revoke active login sessions', path: '/sessions' },
  ];

  return (
    <>
      <style>{sharedCSS}{`
        .dash-profile {
          background:white; border:2px solid var(--pink);
          border-radius:24px; padding:28px 30px;
          margin-bottom:28px; position:relative; overflow:hidden;
        }
        .dash-profile::before {
          content:''; position:absolute;
          top:0; left:0; right:0; height:4px;
          background:linear-gradient(90deg,var(--terra),var(--carnation));
        }
        .dash-avatar {
          width:56px; height:56px;
          background:var(--pink); border-radius:50%;
          display:flex; align-items:center; justify-content:center;
          color:var(--carnation); flex-shrink:0;
        }
        .dash-name {
          font-family:'Playfair Display',serif;
          font-size:1.7rem; font-weight:700; color:var(--dark);
        }
        .dash-email { font-size:0.82rem; color:var(--mid); margin-top:2px; }
        .action-card {
          background:white; border:2px solid var(--pink);
          border-radius:20px; padding:24px;
          cursor:pointer; transition:all .22s;
          position:relative; overflow:hidden;
        }
        .action-card::after {
          content:'→';
          position:absolute; bottom:18px; right:20px;
          font-size:1.1rem; color:var(--pink);
          transition:all .22s;
        }
        .action-card:hover {
          border-color:var(--terra);
          transform:translateY(-4px);
          box-shadow:0 10px 28px rgba(234,120,91,0.18);
        }
        .action-card:hover::after { color:var(--carnation); right:16px; }
        .action-card::before {
          content:''; position:absolute;
          top:0; left:0; right:0; height:3px;
          background:linear-gradient(90deg,var(--terra),var(--carnation));
          transform:scaleX(0); transform-origin:left;
          transition:transform .28s;
        }
        .action-card:hover::before { transform:scaleX(1); }
        .action-icon {
          width:44px; height:44px;
          background:var(--pink); border-radius:13px;
          display:flex; align-items:center; justify-content:center;
          color:var(--carnation); margin-bottom:14px;
        }
        .action-title {
          font-family:'Playfair Display',serif;
          font-size:1.05rem; font-weight:700; color:var(--dark);
          margin-bottom:5px;
        }
        .action-desc { font-size:0.78rem; color:var(--mid); line-height:1.5; }
        .logout-btn {
          display:inline-flex; align-items:center; gap:6px;
          background:none; border:none;
          color:var(--mid); font-family:'DM Sans',sans-serif;
          font-size:0.82rem; cursor:pointer; transition:color .18s;
        }
        .logout-btn:hover { color:var(--carnation); }
      `}</style>

      <div className="pg">
        {/* Nav */}
        <nav className="pg-nav">
          <a href="/" className="pg-logo">FitMe</a>
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={14} /> Logout
          </button>
        </nav>

        <div className="pg-body">
          {/* Profile card */}
          <div className="dash-profile">
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div className="dash-avatar"><User size={26} /></div>
                <div>
                  <div className="dash-name">Welcome back, {user?.name?.split(' ')[0]}!</div>
                  <div className="dash-email">{user?.email}</div>
                </div>
              </div>
            </div>
            <div className="g4 stat-row" style={{ marginBottom: 0 }}>
              {stats.map(s => (
                <div className="stat-card" key={s.label}>
                  <div className="stat-label">{s.label}</div>
                  <div className={`stat-value sm ${s.cls}`} style={{ textTransform: 'capitalize' }}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Action grid */}
          <div className="g4">
            {actions.map(a => (
              <div className="action-card" key={a.title} onClick={() => navigate(a.path)}>
                <div className="action-icon">{a.icon}</div>
                <div className="action-title">{a.title}</div>
                <div className="action-desc">{a.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

export default Dashboard;