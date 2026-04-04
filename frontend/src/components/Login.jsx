import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, KeyRound } from 'lucide-react';
import { loginUser, requestPasswordReset, confirmPasswordReset } from '../services/api';

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=Cormorant+Garamond:ital,wght@0,300;1,300&family=DM+Sans:wght@300;400;500&display=swap');

  :root {
    --terra:    #B08A56;
    --white:    #FFF9FB;
    --pink:     #E9C7D2;
    --carnation:#DFA7BB;
    --peach:    #F4EFEF;
    --dark:     #3A2F35;
    --mid:      #6D5863;
    --mauve:    #B88FA4;
    --wallpaper-url: url('/patterns/bows.jpg');
  }

  .login-wrap {
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    background-color: var(--peach);
    background-image:
      linear-gradient(145deg, rgba(255,249,251,0.78), rgba(244,239,239,0.76)),
      var(--wallpaper-url);
    background-size: 100% 100%, 340px auto;
    background-repeat: no-repeat, repeat;
    background-attachment: fixed, fixed;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }

  .login-pattern {
    position: fixed; inset: 0;
    width: 100%; height: 100%;
    z-index: 0; pointer-events: none;
    display: none;
  }

  .login-back {
    position: fixed;
    top: 24px; left: 24px;
    z-index: 20;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--mid);
    background: white;
    border: 1.5px solid var(--pink);
    border-radius: 50px;
    padding: 7px 16px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'DM Sans', sans-serif;
    border: none;
  }
  .login-back:hover { color: var(--carnation); background: var(--pink); }

  /* CARD */
  .login-card {
    position: relative; z-index: 10;
    width: 460px; max-width: 95vw;
    background: rgba(255, 249, 251, 0.94);
    border-radius: 28px;
    border: 2.5px solid var(--mauve);
    box-shadow: 7px 9px 0 var(--mauve), 0 0 0 7px rgba(233, 199, 210, 0.72);
    overflow: hidden;
    animation: cardIn 0.7s cubic-bezier(.22,1,.36,1) both;
  }
  @keyframes cardIn {
    from { opacity: 0; transform: translateY(28px) scale(.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }

  /* wavy header */
  .login-header {
    background: linear-gradient(180deg, #caa1b4 0%, #b88fa4 100%);
    padding: 28px 32px 44px;
    position: relative;
    text-align: center;
  }
  .login-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0; right: 0;
    height: 36px;
    background: white;
    clip-path: ellipse(58% 100% at 50% 100%);
  }
  .login-brand {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 2rem;
    color: white;
    letter-spacing: -0.5px;
    text-shadow: 2px 2px 0 rgba(0,0,0,0.1);
  }
  .login-tagline {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--peach);
    margin-top: 4px;
  }
  .login-sparkle {
    position: absolute;
    color: var(--peach);
    animation: twinkle 2.5s ease-in-out infinite;
  }
  .login-sparkle.center { top: 22px; left: 40%; font-size: 0.7rem; animation-delay: 0s; }
  .login-sparkle.left { top: 16px; left: 22px; font-size: 0.85rem; animation-delay: 0.9s; }
  .login-sparkle.right { top: 16px; right: 22px; font-size: 0.85rem; animation-delay: 0.5s; }
  @keyframes twinkle {
    0%,100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.35); }
  }

  /* BODY */
  .login-body { padding: 20px 32px 32px; }

  .login-welcome {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 1rem;
    color: var(--mid);
    text-align: center;
    margin-bottom: 22px;
  }

  /* alerts */
  .alert-error {
    background: rgba(241,95,97,0.08);
    border: 1.5px solid var(--carnation);
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 0.83rem;
    color: var(--carnation);
    margin-bottom: 16px;
  }
  .alert-success {
    background: rgba(234,120,91,0.08);
    border: 1.5px solid var(--terra);
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 0.83rem;
    color: var(--terra);
    margin-bottom: 16px;
  }

  /* fields */
  .lf { margin-bottom: 16px; }
  .lf label {
    display: block;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 6px;
    padding-left: 2px;
  }
  .lf input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid var(--pink);
    border-radius: 14px;
    background: rgba(255,190,152,0.08);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    color: var(--dark);
    outline: none;
    transition: all 0.2s;
  }
  .lf input:focus {
    border-color: var(--terra);
    box-shadow: 0 0 0 3px rgba(234,120,91,0.15);
    background: rgba(255,190,152,0.15);
  }
  .lf input::placeholder { color: #C4A090; }

  .forgot-link {
    display: block;
    text-align: right;
    margin-top: -8px;
    margin-bottom: 8px;
    font-size: 0.75rem;
    color: var(--terra);
    font-style: italic;
    cursor: pointer;
    background: none;
    border: none;
    font-family: 'DM Sans', sans-serif;
  }

  /* buttons */
  .btn-primary {
    width: 100%;
    padding: 13px;
    background: var(--carnation);
    border: none;
    border-radius: 50px;
    color: white;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
    font-weight: 500;
    cursor: pointer;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 16px rgba(241,95,97,0.35);
    transition: all 0.2s;
    margin-top: 4px;
  }
  .btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 7px 22px rgba(241,95,97,0.45); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

  .divider-row {
    display: flex; align-items: center; gap: 10px;
    margin: 18px 0 14px;
    color: #C4A090; font-size: 0.72rem; letter-spacing: 1px;
  }
  .divider-row::before,.divider-row::after {
    content:''; flex:1; height:1px; background: var(--pink);
  }

  .btn-google {
    width: 100%;
    padding: 11px;
    background: white;
    border: 2px solid var(--pink);
    border-radius: 50px;
    color: var(--dark);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    transition: all 0.2s;
  }
  .btn-google:hover { border-color: var(--terra); background: rgba(255,190,152,0.1); }

  .login-footer {
    text-align: center;
    margin-top: 20px;
    font-size: 0.82rem;
    color: var(--mid);
  }
  .login-footer button {
    background: none; border: none;
    color: var(--carnation); font-weight: 500;
    cursor: pointer; font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    text-decoration: underline;
    text-decoration-color: rgba(241,95,97,0.4);
  }

  /* reset panel */
  .reset-panel {
    margin-top: 20px;
    border: 2px solid var(--pink);
    border-radius: 18px;
    padding: 18px;
    background: rgba(240,187,180,0.12);
  }
  .reset-panel-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--mid);
    letter-spacing: 0.5px;
    margin-bottom: 14px;
  }
  .btn-outline {
    width: 100%;
    padding: 10px;
    background: white;
    border: 2px solid var(--pink);
    border-radius: 50px;
    color: var(--mid);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.83rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-outline:hover:not(:disabled) { border-color: var(--terra); color: var(--terra); }
  .btn-outline:disabled { opacity: 0.45; cursor: not-allowed; }
  .mt-10 { margin-top: 10px; }
`;

const LoginPattern = () => (
  <svg className="login-pattern" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">
    <defs>
      <pattern id="lpat" x="0" y="0" width="140" height="110" patternUnits="userSpaceOnUse" patternTransform="scale(0.92)">
        {/* Button 4-hole */}
        <g transform="translate(10,10)">
          <circle cx="14" cy="14" r="13" fill="none" stroke="#EA785B" strokeWidth="1.2" />
          <circle cx="10" cy="11" r="1.8" fill="#EA785B" />
          <circle cx="18" cy="11" r="1.8" fill="#EA785B" />
          <circle cx="10" cy="17" r="1.8" fill="#EA785B" />
          <circle cx="18" cy="17" r="1.8" fill="#EA785B" />
        </g>
        {/* Button 2-hole */}
        <g transform="translate(50,8)">
          <circle cx="12" cy="12" r="11" fill="none" stroke="#F15F61" strokeWidth="1.2" />
          <circle cx="9" cy="12" r="1.8" fill="#F15F61" />
          <circle cx="15" cy="12" r="1.8" fill="#F15F61" />
        </g>
        {/* Scissors */}
        <g transform="translate(90,5)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <line x1="0" y1="0" x2="22" y2="22" />
          <line x1="5" y1="0" x2="27" y2="22" />
          <circle cx="2.5" cy="2.5" r="4" />
          <circle cx="24.5" cy="2.5" r="4" />
          <path d="M22,22 Q28,32 22,36 Q16,38 18,30" />
          <path d="M27,22 Q34,32 28,37 Q22,40 21,31" />
        </g>
        {/* Dress sketch */}
        <g transform="translate(140,5)" fill="none" stroke="#F15F61" strokeWidth="1.1">
          <path d="M15,0 Q8,5 5,15 L0,50 L30,50 L25,15 Q22,5 15,0Z" />
          <line x1="5" y1="15" x2="0" y2="50" />
          <line x1="25" y1="15" x2="30" y2="50" />
        </g>
        {/* Bow */}
        <g transform="translate(10,55)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <path d="M15,8 Q2,0 0,8 Q2,16 15,8Z" />
          <path d="M15,8 Q28,0 30,8 Q28,16 15,8Z" />
          <circle cx="15" cy="8" r="3" fill="#EA785B" stroke="none" opacity="0.6" />
        </g>
        {/* Thread spool */}
        <g transform="translate(60,50)" fill="none" stroke="#F0BBB4" strokeWidth="1.1">
          <ellipse cx="14" cy="4" rx="13" ry="3.5" />
          <rect x="1" y="4" width="26" height="18" rx="1" />
          <ellipse cx="14" cy="22" rx="13" ry="3.5" />
          <line x1="5" y1="4" x2="5" y2="22" />
          <line x1="9" y1="4" x2="9" y2="22" />
          <line x1="14" y1="4" x2="14" y2="22" />
          <line x1="19" y1="4" x2="19" y2="22" />
          <line x1="23" y1="4" x2="23" y2="22" />
        </g>
        {/* Shoe */}
        <g transform="translate(105,50)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <path d="M5,18 Q0,14 0,8 Q0,0 10,0 Q20,0 22,8 L34,8 Q38,8 38,16 L5,18Z" />
          <line x1="34" y1="16" x2="34" y2="26" />
          <line x1="31" y1="26" x2="37" y2="26" />
        </g>
        {/* Button ornate */}
        <g transform="translate(155,48)">
          <circle cx="14" cy="14" r="13" fill="none" stroke="#F0BBB4" strokeWidth="1.1" />
          <circle cx="14" cy="14" r="9" fill="none" stroke="#F0BBB4" strokeWidth="0.6" />
          <circle cx="11" cy="12" r="1.5" fill="#F0BBB4" />
          <circle cx="17" cy="12" r="1.5" fill="#F0BBB4" />
          <circle cx="11" cy="17" r="1.5" fill="#F0BBB4" />
          <circle cx="17" cy="17" r="1.5" fill="#F0BBB4" />
        </g>
        {/* Measuring tape */}
        <g transform="translate(5,100)" fill="none" stroke="#EA785B" strokeWidth="1">
          <rect x="0" y="3" width="75" height="9" rx="4.5" />
          {[5, 12, 19, 26, 33, 40, 47, 54, 61, 68].map((x, i) => (
            <line key={i} x1={x} y1="3" x2={x} y2={i % 2 === 0 ? 12 : 10} />
          ))}
        </g>
        {/* Needle */}
        <g transform="translate(100,95)" fill="none" stroke="#F15F61" strokeWidth="1">
          <line x1="4" y1="0" x2="4" y2="45" />
          <ellipse cx="4" cy="4" rx="2.5" ry="4" />
          <path d="M4,45 Q14,35 11,20 Q8,8 4,10" />
        </g>
        {/* Star text */}
        <text x="125" y="120" fontFamily="serif" fontSize="8" fill="#EA785B" fontStyle="italic" opacity="0.7">✦ couture ✦</text>
        {/* Small flowers */}
        <g transform="translate(150,100)">
          {[0, 72, 144, 216, 288].map((deg, i) => (
            <ellipse key={i} cx={12 + 8 * Math.cos(deg * Math.PI / 180)} cy={12 + 8 * Math.sin(deg * Math.PI / 180)} rx="3.5" ry="2" fill="none" stroke="#F0BBB4" strokeWidth="0.9"
              transform={`rotate(${deg} ${12 + 8 * Math.cos(deg * Math.PI / 180)} ${12 + 8 * Math.sin(deg * Math.PI / 180)})`} />
          ))}
          <circle cx="12" cy="12" r="3" fill="none" stroke="#EA785B" strokeWidth="0.9" />
        </g>
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#lpat)" />
  </svg>
);

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showReset, setShowReset] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [resetMessage, setResetMessage] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  const handleSignIn = async () => {
    setLoading(true); setError('');
    try {
      await loginUser(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to sign in. Please try again.');
    } finally { setLoading(false); }
  };

  const handleRequestReset = async () => {
    setResetLoading(true); setError(''); setResetMessage('');
    try {
      const response = await requestPasswordReset(resetEmail || email);
      setResetMessage(response.data?.detail || 'If that email is registered, reset instructions were sent.');
      if (response.data?.reset_token) setResetToken(response.data.reset_token);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to request reset right now.');
    } finally { setResetLoading(false); }
  };

  const handleConfirmReset = async () => {
    setResetLoading(true); setError('');
    try {
      await confirmPasswordReset(resetToken, newPassword);
      setResetMessage('Password reset successful. You can now sign in.');
      setShowReset(false); setPassword(''); setNewPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to reset password.');
    } finally { setResetLoading(false); }
  };

  return (
    <>
      <style>{css}</style>
      <div className="login-wrap">
        <button className="login-back" onClick={() => navigate('/')}>
          <ArrowLeft size={14} /> Back
        </button>

        <div className="login-card">
          {/* Header */}
          <div className="login-header">
            <span className="login-sparkle left">✦</span>
            <span className="login-sparkle right">✦</span>
            <span className="login-sparkle center">✦</span>
            <div className="login-brand">FitMe</div>
            <div className="login-tagline">your personal fashion assistant</div>
          </div>

          {/* Body */}
          <div className="login-body">
            <p className="login-welcome">Welcome back, darling ✨</p>

            {error && <div className="alert-error">{error}</div>}
            {resetMessage && <div className="alert-success">{resetMessage}</div>}

            <div className="lf">
              <label>Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <div className="lf">
              <label>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            </div>

            <button className="forgot-link" onClick={() => { setShowReset(v => !v); setError(''); setResetMessage(''); }}>
              Forgot password?
            </button>

            <button className="btn-primary" onClick={handleSignIn} disabled={!email || !password || loading}>
              {loading ? 'Signing in…' : 'Sign In →'}
            </button>

            <div className="divider-row">or continue with</div>

            <button className="btn-google">
              <svg width="17" height="17" viewBox="0 0 18 18"><path d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z" fill="#4285F4" /><path d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2.02c-.72.48-1.63.77-2.7.77a4.85 4.85 0 01-4.57-3.35H1.73v2.08A8 8 0 008.98 17z" fill="#34A853" /><path d="M4.41 10.46A4.93 4.93 0 014.16 9c0-.51.09-1 .25-1.46V5.46H1.73A8 8 0 001 9c0 1.29.31 2.51.73 3.54l2.68-2.08z" fill="#FBBC05" /><path d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2L14.3 3.1A7.98 7.98 0 008.98 1C6 1 3.41 2.7 1.73 5.46l2.68 2.08a4.84 4.84 0 014.57-3.36z" fill="#EA4335" /></svg>
              Continue with Google
            </button>

            {showReset && (
              <div className="reset-panel">
                <div className="reset-panel-title"><KeyRound size={14} /> Reset Password</div>
                <div className="lf">
                  <label>Email for reset</label>
                  <input type="email" value={resetEmail} onChange={e => setResetEmail(e.target.value)} placeholder="your@email.com" />
                </div>
                <button className="btn-outline" onClick={handleRequestReset} disabled={(!resetEmail && !email) || resetLoading}>
                  {resetLoading ? 'Requesting…' : 'Send Reset Link'}
                </button>
                <div className="lf mt-10">
                  <label>Reset Token</label>
                  <input type="text" value={resetToken} onChange={e => setResetToken(e.target.value)} placeholder="Paste token from email" />
                </div>
                <div className="lf">
                  <label>New Password</label>
                  <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="New password" />
                </div>
                <button className="btn-primary" onClick={handleConfirmReset} disabled={!resetToken || !newPassword || resetLoading}
                  style={{ marginTop: 4 }}>
                  {resetLoading ? 'Resetting…' : 'Confirm Reset'}
                </button>
              </div>
            )}

            <div className="login-footer">
              New here? <button onClick={() => navigate('/onboarding')}>Create an account</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default Login;