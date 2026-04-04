import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, User as UserIcon, Ruler, Weight, ArrowLeft } from 'lucide-react';
import { createUser, analyzeUser, loginUser, confirmEmailVerification, resendEmailVerification } from '../services/api';

const GMAIL_PATTERN = /^[a-z0-9](?:[a-z0-9._%+-]{0,61}[a-z0-9])?@gmail\.com$/i;

const isValidGmailAddress = (value) => {
  const email = (value || '').trim().toLowerCase();
  if (!GMAIL_PATTERN.test(email)) return false;
  return !email.split('@', 1)[0].includes('..');
};

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

  .ob-wrap {
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
    align-items: flex-start;
    justify-content: center;
    padding: 32px 24px 60px;
    position: relative;
    overflow-x: hidden;
  }

  .ob-pattern {
    position: fixed; inset: 0;
    width: 100%; height: 100%;
    z-index: 0; pointer-events: none;
    display: none;
  }

  .ob-back {
    position: fixed;
    top: 24px; left: 24px; z-index: 20;
    display: inline-flex; align-items: center; gap: 6px;
    color: var(--mid);
    background: white;
    border: 1.5px solid var(--pink);
    border-radius: 50px;
    padding: 7px 16px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'DM Sans', sans-serif;
  }
  .ob-back:hover { color: var(--carnation); border-color: var(--carnation); }

  .ob-card {
    position: relative; z-index: 10;
    width: 560px; max-width: 95vw;
    margin-top: 32px;
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

  /* header */
  .ob-header {
    background: linear-gradient(180deg, #caa1b4 0%, #b88fa4 100%);
    padding: 22px 32px 42px;
    position: relative;
    text-align: center;
  }
  .ob-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0; right: 0;
    height: 34px;
    background: white;
    clip-path: ellipse(58% 100% at 50% 100%);
  }
  .ob-sparkle {
    position: absolute;
    color: var(--peach);
    animation: twinkle 2.5s ease-in-out infinite;
  }
  .ob-sparkle.center { top: 18px; left: 43%; font-size: 0.7rem; animation-delay: 0s; }
  .ob-sparkle.left { top: 14px; left: 18px; font-size: 0.85rem; animation-delay: 0.9s; }
  .ob-sparkle.right { top: 14px; right: 18px; font-size: 0.85rem; animation-delay: 0.5s; }
  @keyframes twinkle {
    0%,100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.35); }
  }
  .ob-brand {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.8rem;
    color: white;
    text-shadow: 2px 2px 0 rgba(0,0,0,0.1);
  }
  .ob-tagline {
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--peach);
    margin-top: 3px;
    font-family: 'DM Sans', sans-serif;
  }

  /* tabs */
  .ob-tabs {
    display: flex;
    margin: 24px 32px 0;
    background: var(--pink);
    border-radius: 50px;
    padding: 4px;
    gap: 4px;
  }
  .ob-tab {
    flex: 1;
    padding: 9px;
    border: none;
    border-radius: 50px;
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--mid);
    cursor: pointer;
    transition: all 0.25s;
  }
  .ob-tab.active {
    background: var(--carnation);
    color: white;
    box-shadow: 0 2px 10px rgba(241,95,97,0.35);
  }

  /* steps indicator */
  .ob-steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    padding: 20px 32px 0;
  }
  .ob-step-dot {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Playfair Display', serif;
    font-size: 0.9rem;
    font-weight: 700;
    border: 2px solid var(--pink);
    color: var(--mid);
    background: white;
    transition: all 0.3s;
    position: relative; z-index: 1;
  }
  .ob-step-dot.done {
    background: var(--terra);
    border-color: var(--terra);
    color: white;
  }
  .ob-step-dot.active {
    background: var(--carnation);
    border-color: var(--carnation);
    color: white;
    box-shadow: 0 0 0 4px rgba(241,95,97,0.2);
  }
  .ob-step-line {
    flex: 1;
    height: 2px;
    background: var(--pink);
    margin: 0 -1px;
    transition: background 0.3s;
  }
  .ob-step-line.done { background: var(--terra); }
  .ob-step-labels {
    display: flex;
    justify-content: space-between;
    padding: 6px 24px 0;
  }
  .ob-step-label {
    font-size: 0.62rem;
    letter-spacing: 0.5px;
    color: var(--mid);
    text-align: center;
    flex: 1;
    opacity: 0.7;
  }
  .ob-step-label.active { opacity: 1; color: var(--carnation); font-weight: 500; }

  /* body */
  .ob-body { padding: 20px 32px 36px; }

  .ob-welcome {
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

  /* fields */
  .of { margin-bottom: 16px; }
  .of label {
    display: flex; align-items: center; gap: 5px;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 6px;
    padding-left: 2px;
  }
  .of input[type="text"],
  .of input[type="email"],
  .of input[type="password"],
  .of input[type="number"] {
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
  .of input:focus {
    border-color: var(--terra);
    box-shadow: 0 0 0 3px rgba(234,120,91,0.15);
    background: rgba(255,190,152,0.15);
  }
  .of input::placeholder { color: #C4A090; }

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

  /* upload zone */
  .upload-zone {
    border: 2px dashed var(--pink);
    border-radius: 18px;
    padding: 36px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: rgba(255,190,152,0.05);
    position: relative;
  }
  .upload-zone:hover { border-color: var(--terra); background: rgba(255,190,152,0.12); }
  .upload-zone-icon { color: var(--pink); margin-bottom: 10px; }
  .upload-zone-title { font-size: 0.9rem; color: var(--mid); font-weight: 500; }
  .upload-zone-sub { font-size: 0.75rem; color: #C4A090; margin-top: 4px; }
  .upload-preview { max-height: 200px; border-radius: 12px; object-fit: cover; }

  /* review */
  .review-box {
    background: var(--white);
    border: 2px solid var(--pink);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
  }
  .review-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    color: var(--dark);
    margin-bottom: 16px;
    font-style: italic;
  }
  .review-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .review-item p:first-child { font-size: 0.68rem; letter-spacing: 1px; text-transform: uppercase; color: #C4A090; margin-bottom: 2px; }
  .review-item p:last-child { font-size: 0.9rem; color: var(--dark); font-weight: 500; }

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
  }
  .btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 7px 22px rgba(241,95,97,0.45); }
  .btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }

  .btn-secondary {
    flex: 1;
    padding: 13px;
    background: var(--white);
    border: 2px solid var(--pink);
    border-radius: 50px;
    color: var(--mid);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-secondary:hover:not(:disabled) { border-color: var(--terra); color: var(--terra); }
  .btn-secondary:disabled { opacity: 0.45; cursor: not-allowed; }

  .btn-row { display: flex; gap: 12px; }

  .ob-footer {
    text-align: center;
    margin-top: 18px;
    font-size: 0.82rem;
    color: var(--mid);
  }
  .ob-footer button {
    background: none; border: none;
    color: var(--carnation); font-weight: 500;
    cursor: pointer; font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    text-decoration: underline;
    text-decoration-color: rgba(241,95,97,0.4);
  }

  /* signin mode */
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
    display: flex; align-items: center; justify-content: center; gap: 10px;
    transition: all 0.2s;
  }
  .btn-google:hover { border-color: var(--terra); background: rgba(255,190,152,0.1); }
`;

const ObPattern = () => (
  <svg className="ob-pattern" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400" preserveAspectRatio="xMidYMid slice">
    <defs>
      <pattern id="obpat" x="0" y="0" width="150" height="120" patternUnits="userSpaceOnUse" patternTransform="scale(0.95)">
        {/* Dress on mannequin */}
        <g transform="translate(15,10)" fill="none" stroke="#EA785B" strokeWidth="1.2">
          <line x1="18" y1="0" x2="18" y2="8" />
          <ellipse cx="18" cy="11" rx="5" ry="3.5" />
          <path d="M13,14 Q8,24 10,36 Q18,40 26,36 Q28,24 23,14" />
          <path d="M10,36 Q10,50 13,52 L23,52 Q26,50 26,36" />
          <line x1="18" y1="52" x2="18" y2="60" />
          <ellipse cx="18" cy="62" rx="7" ry="2.5" />
          {/* dress bow */}
          <path d="M13,20 Q18,16 23,20 Q18,24 13,20Z" fill="#F15F61" stroke="none" opacity="0.6" />
        </g>
        {/* Ruffled skirt */}
        <g transform="translate(55,8)" fill="none" stroke="#F15F61" strokeWidth="1.1">
          <path d="M15,0 Q8,4 5,12 L0,45 Q15,52 30,45 L25,12 Q22,4 15,0Z" />
          <path d="M2,25 Q15,30 28,25" />
          <path d="M1,35 Q15,40 29,35" />
          <path d="M0,45 Q15,52 30,45" />
        </g>
        {/* Scissors fancy */}
        <g transform="translate(105,10)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <line x1="0" y1="0" x2="24" y2="24" />
          <line x1="5" y1="0" x2="29" y2="24" />
          <circle cx="2.5" cy="2.5" r="5" />
          <circle cx="26.5" cy="2.5" r="5" />
          <path d="M24,24 Q30,34 23,38 Q17,40 20,32" />
          <path d="M29,24 Q36,34 29,39 Q23,42 22,33" />
        </g>
        {/* High heel shoe */}
        <g transform="translate(155,15)" fill="none" stroke="#F15F61" strokeWidth="1.1">
          <path d="M5,20 Q0,15 0,8 Q0,0 12,0 Q22,0 24,8 L38,8 Q42,8 42,18 L5,20Z" />
          <line x1="38" y1="18" x2="38" y2="28" />
          <line x1="35" y1="28" x2="41" y2="28" />
          <circle cx="10" cy="6" r="1.5" fill="#F15F61" stroke="none" />
          <circle cx="18" cy="4" r="1.5" fill="#F15F61" stroke="none" />
        </g>
        {/* Handbag */}
        <g transform="translate(205,10)" fill="none" stroke="#F0BBB4" strokeWidth="1.1">
          <path d="M4,18 Q0,18 0,26 L0,48 Q0,52 4,52 L36,52 Q40,52 40,48 L40,26 Q40,18 36,18Z" />
          <path d="M12,18 Q12,10 20,10 Q28,10 28,18" />
          <line x1="0" y1="30" x2="40" y2="30" />
          <rect x="15" y="24" width="10" height="10" rx="2" stroke="#EA785B" />
        </g>
        {/* Thread spool */}
        <g transform="translate(10,85)" fill="none" stroke="#F0BBB4" strokeWidth="1.1">
          <ellipse cx="16" cy="5" rx="15" ry="4" />
          <rect x="1" y="5" width="30" height="22" rx="1" />
          <ellipse cx="16" cy="27" rx="15" ry="4" />
          {[4, 8, 12, 16, 20, 24, 28].map((x, i) => (
            <line key={i} x1={x} y1="5" x2={x} y2="27" />
          ))}
        </g>
        {/* Bow ornament */}
        <g transform="translate(60,82)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <path d="M18,9 Q3,0 0,9 Q3,18 18,9Z" />
          <path d="M18,9 Q33,0 36,9 Q33,18 18,9Z" />
          <circle cx="18" cy="9" r="3.5" fill="#EA785B" stroke="none" opacity="0.65" />
          <line x1="18" y1="12.5" x2="18" y2="28" />
          <path d="M18,28 Q12,34 14,38 M18,28 Q24,34 22,38" />
        </g>
        {/* Buttons */}
        <g transform="translate(110,80)">
          <circle cx="14" cy="14" r="13" fill="none" stroke="#EA785B" strokeWidth="1.2" />
          <circle cx="10" cy="11" r="2" fill="#EA785B" />
          <circle cx="18" cy="11" r="2" fill="#EA785B" />
          <circle cx="10" cy="17" r="2" fill="#EA785B" />
          <circle cx="18" cy="17" r="2" fill="#EA785B" />
          <path d="M10,11 L18,17 M18,11 L10,17" stroke="#EA785B" strokeWidth="0.7" />
        </g>
        <g transform="translate(148,84)">
          <circle cx="12" cy="12" r="11" fill="none" stroke="#F15F61" strokeWidth="1.1" />
          <circle cx="12" cy="9" r="1.8" fill="#F15F61" />
          <circle cx="12" cy="15" r="1.8" fill="#F15F61" />
          <circle cx="9" cy="12" r="1.8" fill="#F15F61" />
          <circle cx="15" cy="12" r="1.8" fill="#F15F61" />
        </g>
        {/* Flower */}
        <g transform="translate(185,85)">
          {[0, 60, 120, 180, 240, 300].map((deg, i) => (
            <ellipse key={i}
              cx={18 + 10 * Math.cos(deg * Math.PI / 180)}
              cy={18 + 10 * Math.sin(deg * Math.PI / 180)}
              rx="4.5" ry="2.5" fill="none" stroke="#F0BBB4" strokeWidth="0.9"
              transform={`rotate(${deg} ${18 + 10 * Math.cos(deg * Math.PI / 180)} ${18 + 10 * Math.sin(deg * Math.PI / 180)})`} />
          ))}
          <circle cx="18" cy="18" r="4" fill="none" stroke="#EA785B" strokeWidth="0.9" />
        </g>
        {/* Measuring tape */}
        <g transform="translate(5,140)" fill="none" stroke="#EA785B" strokeWidth="1">
          <rect x="0" y="3" width="90" height="9" rx="4.5" />
          {[6, 14, 22, 30, 38, 46, 54, 62, 70, 78, 86].map((x, i) => (
            <line key={i} x1={x} y1="3" x2={x} y2={i % 2 === 0 ? 12 : 10} />
          ))}
        </g>
        {/* Needle */}
        <g transform="translate(110,135)" fill="none" stroke="#F15F61" strokeWidth="1">
          <line x1="4" y1="0" x2="4" y2="48" />
          <ellipse cx="4" cy="4" rx="2.5" ry="4.5" />
          <path d="M4,48 Q15,38 12,22 Q9,8 4,12" />
        </g>
        {/* Umbrella / parasol dainty */}
        <g transform="translate(140,130)" fill="none" stroke="#F0BBB4" strokeWidth="1.1">
          <path d="M30,0 Q60,5 60,20 Q50,15 30,15 Q10,15 0,20 Q0,5 30,0Z" />
          <line x1="30" y1="15" x2="30" y2="55" />
          <path d="M28,55 Q30,60 32,55" />
          {[0, 15, 30, 45, 60].map((x, i) => (
            <line key={i} x1={30} y1="0" x2={x} y2="20" />
          ))}
        </g>
        {/* Script text */}
        <text x="200" y="160" fontFamily="serif" fontSize="9" fill="#EA785B" fontStyle="italic" opacity="0.65">Paris ✦</text>
        <text x="15" y="175" fontFamily="serif" fontSize="7.5" fill="#F0BBB4" letterSpacing="1.5" opacity="0.7">✦ couture ✦</text>
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#obpat)" />
  </svg>
);

function Onboarding() {
  const navigate = useNavigate();
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const [authMode, setAuthMode] = useState(params.get('mode') === 'signin' ? 'signin' : 'signup');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [verificationPending, setVerificationPending] = useState(false);
  const [verificationToken, setVerificationToken] = useState('');
  const [verificationEmail, setVerificationEmail] = useState('');
  const [verificationMessage, setVerificationMessage] = useState('');

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) { setImage(file); setImagePreview(URL.createObjectURL(file)); }
  };

  const handleSubmit = async () => {
    setLoading(true); setError('');
    try {
      if (authMode === 'signin') {
        await loginUser(email, password);
        navigate('/dashboard');
        return;
      }
      if (!isValidGmailAddress(email)) {
        throw new Error('Email not valid. Please use a real Gmail address.');
      }
      const userResponse = await createUser(name, email, password);
      setVerificationPending(true);
      setVerificationEmail(userResponse.data?.email || email);
      setVerificationToken(userResponse.data?.verification_token || '');
      setVerificationMessage(userResponse.data?.detail || 'Check your Gmail for the confirmation code.');
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.');
    } finally { setLoading(false); }
  };

  const handleConfirmEmail = async () => {
    setLoading(true); setError('');
    try {
      const response = await confirmEmailVerification(verificationToken);
      setVerificationMessage(response.data?.detail || 'Email confirmed.');
      const loginResponse = await loginUser(email, password);
      await analyzeUser(loginResponse.data.user_id, image, parseFloat(height), parseFloat(weight));
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to confirm your email.');
    } finally { setLoading(false); }
  };

  const handleResendVerification = async () => {
    setLoading(true); setError(''); setVerificationMessage('');
    try {
      const response = await resendEmailVerification(email);
      setVerificationMessage(response.data?.detail || 'A new confirmation code was sent.');
      if (response.data?.verification_token) {
        setVerificationToken(response.data.verification_token);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to resend verification email right now.');
    } finally { setLoading(false); }
  };

  const stepLabels = ['Account', 'Your Body', 'Review'];

  return (
    <>
      <style>{css}</style>
      <div className="ob-wrap">
        <button className="ob-back" onClick={() => navigate('/')}>
          <ArrowLeft size={14} /> Back
        </button>

        <div className="ob-card">
          {/* Header */}
          <div className="ob-header">
            <span className="ob-sparkle left">✦</span>
            <span className="ob-sparkle right">✦</span>
            <span className="ob-sparkle center">✦</span>
            <div className="ob-brand">FitMe</div>
            <div className="ob-tagline">your personal fashion assistant</div>
          </div>

          {/* Tabs */}
          <div className="ob-tabs">
            <button className={`ob-tab ${authMode === 'signup' ? 'active' : ''}`} onClick={() => { setAuthMode('signup'); setStep(1); setError(''); }}>
              Create Account
            </button>
            <button className={`ob-tab ${authMode === 'signin' ? 'active' : ''}`} onClick={() => { setAuthMode('signin'); setStep(1); setError(''); }}>
              Sign In
            </button>
          </div>

          {/* Step indicator (signup only) */}
          {authMode === 'signup' && (
            <>
              <div className="ob-steps">
                {[1, 2, 3].map((s) => (
                  <div key={s} style={{ display: 'flex', alignItems: 'center', flex: s < 3 ? 1 : 'none' }}>
                    <div className={`ob-step-dot ${step > s ? 'done' : step === s ? 'active' : ''}`}>{s}</div>
                    {s < 3 && <div className={`ob-step-line ${step > s ? 'done' : ''}`} />}
                  </div>
                ))}
              </div>
              <div className="ob-step-labels">
                {stepLabels.map((l, i) => (
                  <span key={l} className={`ob-step-label ${step === i + 1 ? 'active' : ''}`}>{l}</span>
                ))}
              </div>
            </>
          )}

          {/* Body */}
          <div className="ob-body">
            {error && <div className="alert-error">{error}</div>}
            {verificationMessage && <div className="alert-success">{verificationMessage}</div>}

            {verificationPending && (
              <div className="review-box" style={{ marginBottom: 18 }}>
                <div className="review-title">Confirm your Gmail</div>
                <p className="ob-welcome" style={{ marginBottom: 12 }}>
                  We sent a confirmation code to {verificationEmail || email}. Paste it below to finish creating your account.
                </p>
                <div className="of">
                  <label>Confirmation Code</label>
                  <input
                    type="text"
                    value={verificationToken}
                    onChange={e => setVerificationToken(e.target.value)}
                    placeholder="Paste the confirmation code"
                  />
                </div>
                <div className="btn-row">
                  <button className="btn-secondary" onClick={handleResendVerification} disabled={loading}>
                    {loading ? 'Sending…' : 'Resend Code'}
                  </button>
                  <button className="btn-primary" onClick={handleConfirmEmail} disabled={!verificationToken || loading} style={{ flex: 1 }}>
                    {loading ? 'Confirming…' : 'Confirm Email'}
                  </button>
                </div>
                {verificationToken && (
                  <p style={{ marginTop: 12, fontSize: '0.8rem', color: 'var(--mid)' }}>
                    Dev code: <strong>{verificationToken}</strong>
                  </p>
                )}
              </div>
            )}

            {/* ── SIGN IN ── */}
            {authMode === 'signin' && (
              <>
                <p className="ob-welcome">Welcome back, darling ✨</p>
                <div className="of">
                  <label>Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
                </div>
                <div className="of">
                  <label>Password</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
                </div>
                <button className="btn-primary" onClick={handleSubmit} disabled={!email || !password || loading}>
                  {loading ? 'Signing In…' : 'Sign In →'}
                </button>
                <div className="divider-row">or continue with</div>
                <button className="btn-google">
                  <svg width="17" height="17" viewBox="0 0 18 18"><path d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z" fill="#4285F4" /><path d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2.02c-.72.48-1.63.77-2.7.77a4.85 4.85 0 01-4.57-3.35H1.73v2.08A8 8 0 008.98 17z" fill="#34A853" /><path d="M4.41 10.46A4.93 4.93 0 014.16 9c0-.51.09-1 .25-1.46V5.46H1.73A8 8 0 001 9c0 1.29.31 2.51.73 3.54l2.68-2.08z" fill="#FBBC05" /><path d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2L14.3 3.1A7.98 7.98 0 008.98 1C6 1 3.41 2.7 1.73 5.46l2.68 2.08a4.84 4.84 0 014.57-3.36z" fill="#EA4335" /></svg>
                  Continue with Google
                </button>
                <div className="ob-footer">
                  New here? <button onClick={() => { setAuthMode('signup'); setStep(1); }}>Create an account</button>
                </div>
              </>
            )}

            {/* ── STEP 1: Basic Info ── */}
            {authMode === 'signup' && step === 1 && (
              <>
                <p className="ob-welcome">Let's build your style profile ✨</p>
                <div className="of">
                  <label><UserIcon size={11} /> Full Name</label>
                  <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Enter your name" />
                </div>
                <div className="of">
                  <label>Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
                </div>
                <div className="of">
                  <label>Password</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 8 chars, upper/lowercase & number" />
                </div>
                <button className="btn-primary" onClick={() => {
                  if (!isValidGmailAddress(email)) {
                    setError('Email not valid. Please use a real Gmail address.');
                    return;
                  }
                  setStep(2);
                }} disabled={!name || !email || !password}>
                  Continue →
                </button>
                <div className="ob-footer" style={{ marginTop: 16 }}>
                  Already have an account? <button onClick={() => { setAuthMode('signin'); }}>Sign In</button>
                </div>
              </>
            )}

            {/* ── STEP 2: Photo & Measurements ── */}
            {authMode === 'signup' && step === 2 && (
              <>
                <p className="ob-welcome">Tell us about your beautiful self ✨</p>
                <div className="of">
                  <label><Upload size={11} /> Full Body Photo</label>
                  <div className="upload-zone">
                    <input type="file" accept="image/*" onChange={handleImageChange} style={{ display: 'none' }} id="photo-upload" />
                    <label htmlFor="photo-upload" style={{ cursor: 'pointer', display: 'block' }}>
                      {imagePreview
                        ? <img src={imagePreview} alt="Preview" className="upload-preview" style={{ margin: '0 auto', display: 'block' }} />
                        : <>
                          <div className="upload-zone-icon"><Upload size={36} style={{ margin: '0 auto', color: 'var(--pink)' }} /></div>
                          <div className="upload-zone-title">Click to upload or drag & drop</div>
                          <div className="upload-zone-sub">PNG, JPG up to 10MB</div>
                        </>
                      }
                    </label>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="of">
                    <label><Ruler size={11} /> Height (cm)</label>
                    <input type="number" value={height} onChange={e => setHeight(e.target.value)} placeholder="170" />
                  </div>
                  <div className="of">
                    <label><Weight size={11} /> Weight (kg)</label>
                    <input type="number" value={weight} onChange={e => setWeight(e.target.value)} placeholder="65" />
                  </div>
                </div>
                <div className="btn-row">
                  <button className="btn-secondary" onClick={() => setStep(1)}>← Back</button>
                  <button className="btn-primary" onClick={() => setStep(3)} disabled={!image || !height || !weight}
                    style={{ flex: 1 }}>
                    Continue →
                  </button>
                </div>
              </>
            )}

            {/* ── STEP 3: Review ── */}
            {authMode === 'signup' && step === 3 && (
              <>
                <p className="ob-welcome">Almost there — looking gorgeous! ✨</p>
                <div className="review-box">
                  <div className="review-title">Your Profile Summary</div>
                  <div className="review-grid">
                    <div className="review-item"><p>Name</p><p>{name}</p></div>
                    <div className="review-item"><p>Email</p><p style={{ wordBreak: 'break-all' }}>{email}</p></div>
                    <div className="review-item"><p>Password</p><p>{'•'.repeat(Math.min(password.length, 12))}</p></div>
                    <div className="review-item"><p>Height</p><p>{height} cm</p></div>
                    <div className="review-item"><p>Weight</p><p>{weight} kg</p></div>
                  </div>
                  {imagePreview && (
                    <div style={{ marginTop: 16 }}>
                      <p style={{ fontSize: '0.68rem', letterSpacing: '1px', textTransform: 'uppercase', color: '#C4A090', marginBottom: 8 }}>Photo</p>
                      <img src={imagePreview} alt="Preview" style={{ maxHeight: 140, borderRadius: 12, objectFit: 'cover' }} />
                    </div>
                  )}
                </div>
                <div className="btn-row">
                  <button className="btn-secondary" onClick={() => setStep(2)} disabled={loading}>← Back</button>
                  <button className="btn-primary" onClick={handleSubmit} disabled={loading}
                    style={{ flex: 1 }}>
                    {loading ? 'Setting up your wardrobe…' : 'Complete Setup ✦'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default Onboarding;