import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, RefreshCw, LogOut, ArrowLeft, Clock, Monitor } from 'lucide-react';
import { getAuthSessions, revokeAuthSession, logoutAllDevices } from '../services/api';
import { sharedCSS } from './sharedStyles';

const fmtDate = (v) => {
  if (!v) return '—';
  const d = new Date(v);
  return isNaN(d.getTime()) ? '—' : d.toLocaleString();
};
const trimUA = (ua) => !ua ? 'Unknown device' : ua.length > 60 ? `${ua.slice(0, 60)}…` : ua;

function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [activeCount, setActiveCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyToken, setBusyToken] = useState('');

  const totalCount = useMemo(() => sessions.length, [sessions]);

  const loadSessions = async () => {
    setLoading(true); setError('');
    try {
      const r = await getAuthSessions();
      setSessions(r.data.sessions || []);
      setActiveCount(r.data.active_sessions || 0);
    } catch (e) {
      setError(e.response?.data?.detail || 'Unable to load sessions.');
    } finally { setLoading(false); }
  };

  useEffect(() => { loadSessions(); }, []);

  const handleRevoke = async (jti) => {
    setBusyToken(jti); setError('');
    try { await revokeAuthSession(jti); await loadSessions(); }
    catch (e) { setError(e.response?.data?.detail || 'Unable to revoke session.'); }
    finally { setBusyToken(''); }
  };

  const handleLogoutAll = async () => {
    setBusyToken('logout-all'); setError('');
    try { await logoutAllDevices(); navigate('/'); }
    catch (e) { setError(e.response?.data?.detail || 'Unable to logout all devices.'); setBusyToken(''); }
  };

  return (
    <>
      <style>{sharedCSS}</style>
      <div className="pg">
        <nav className="pg-nav">
          <div className="pg-nav-left">
            <button className="pg-back" onClick={() => navigate('/dashboard')}><ArrowLeft size={13} /> Dashboard</button>
            <span className="pg-title"><Shield size={15} className="pg-title-icon" /> Security Sessions</span>
          </div>
          <button className="btn-s" onClick={loadSessions} disabled={loading || busyToken === 'logout-all'}
            style={{ padding: '6px 14px', fontSize: '0.78rem' }}>
            <RefreshCw size={13} /> Refresh
          </button>
        </nav>

        <div className="pg-body-narrow">
          {/* Summary card */}
          <div className="wcard" style={{ marginBottom: 20 }}>
            <div className="wcard-head sessions-hero-head">
              <div className="wcard-head-title">Session Management</div>
              <div className="wcard-head-sub sessions-hero-sub">Review active sessions and revoke devices you don&apos;t trust</div>
            </div>
            <div className="wcard-pad" style={{ paddingTop: 36 }}>
              <div className="g2 stat-row" style={{ marginBottom: 20 }}>
                <div className="stat-card">
                  <div className="stat-label">Total Sessions</div>
                  <div className="stat-value">{totalCount}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Active</div>
                  <div className="stat-value stat-green">{activeCount}</div>
                </div>
              </div>
              <button className="btn-danger" onClick={handleLogoutAll}
                disabled={busyToken === 'logout-all' || loading || activeCount === 0}>
                <LogOut size={13} />
                {busyToken === 'logout-all' ? 'Logging out all…' : 'Logout All Devices'}
              </button>
            </div>
          </div>

          {error && <div className="alert-e">{error}</div>}

          {/* Sessions list */}
          {loading ? (
            <div className="wcard wcard-pad" style={{ color: 'var(--mid)', fontStyle: 'italic', fontFamily: 'Cormorant Garamond,serif' }}>
              Loading sessions…
            </div>
          ) : sessions.length === 0 ? (
            <div className="wcard wcard-pad" style={{ textAlign: 'center', color: 'var(--mid)' }}>
              No sessions found.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {sessions.map(s => (
                <div key={s.jti} className={`session-card ${s.is_active ? 'active-s' : ''}`}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                    <div style={{ flex: 1 }}>
                      <div className="session-ua">
                        <Monitor size={14} style={{ color: 'var(--terra)', flexShrink: 0 }} />
                        {trimUA(s.user_agent)}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#C4A090', margin: '4px 0 8px' }}>
                        IP: {s.ip_address || 'Unknown'} · ID: {s.jti?.slice(0, 16)}…
                      </div>
                      <div className="session-meta">
                        <span><Clock size={11} /> Created: {fmtDate(s.created_at)}</span>
                        <span>Last used: {fmtDate(s.last_used_at)}</span>
                        <span>Expires: {fmtDate(s.expires_at)}</span>
                        <span>Revoked: {fmtDate(s.revoked_at)}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
                      <span className={`pill ${s.is_active ? 'pill-green' : 'pill-gray'}`}>
                        {s.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <button className="btn-danger"
                        style={{ fontSize: '0.75rem', padding: '6px 12px' }}
                        onClick={() => handleRevoke(s.jti)}
                        disabled={!s.is_active || busyToken === s.jti || busyToken === 'logout-all'}>
                        {busyToken === s.jti ? 'Revoking…' : 'Revoke'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default Sessions;