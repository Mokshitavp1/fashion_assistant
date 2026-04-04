import { useNavigate } from 'react-router-dom';
import { Sparkles, Shirt, ShoppingBag, Trash2, User } from 'lucide-react';

// ── Inline styles & keyframes injected once ──────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');

  :root {
    --terra:    #B08A56;
    --white:    #FFF9FB;
    --pink:     #E9C7D2;
    --carnation:#DFA7BB;
    --peach:    #F4EFEF;
    --dark:     #3A2F35;
    --mid:      #6D5863;
    --deep:     #5A4751;
    --wallpaper-url: url('/patterns/landing_page_design.jpg');
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  .lp-body {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--peach);
    background-image:
      linear-gradient(145deg, rgba(255,249,251,0.52), rgba(233,199,210,0.16)),
      var(--wallpaper-url);
    background-size: 100% 100%, 360px auto;
    background-repeat: no-repeat, repeat;
    background-attachment: fixed, fixed;
    color: var(--dark);
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
  }

  /* ── Pattern SVG BG ── */
  .lp-pattern {
    position: fixed;
    inset: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
    display: none;
  }

  /* ── NAV ── */
  .lp-nav {
    position: relative; z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 48px;
    border-bottom: 1.5px solid rgba(184,143,164,0.3);
    background: rgba(255,249,251,0.88);
    backdrop-filter: blur(8px);
  }
  .lp-logo {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.8rem;
    color: var(--terra);
    letter-spacing: -0.5px;
  }
  .lp-logo span { color: var(--carnation); font-style: normal; }
  .lp-nav-btns { display: flex; gap: 12px; }
  .btn-ghost {
    padding: 9px 22px;
    border: 2px solid var(--terra);
    border-radius: 50px;
    background: transparent;
    color: var(--terra);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.5px;
  }
  .btn-ghost:hover { background: var(--terra); color: white; }
  .btn-fill {
    padding: 9px 22px;
    border: 2px solid var(--carnation);
    border-radius: 50px;
    background: var(--carnation);
    color: white;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 14px rgba(241,95,97,0.35);
  }
  .btn-fill:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(241,95,97,0.45); }

  /* ── HERO ── */
  .lp-hero {
    position: relative; z-index: 5;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 80px 24px 60px;
  }
  .lp-hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--pink);
    border: 1.5px solid var(--terra);
    border-radius: 50px;
    padding: 6px 16px;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 28px;
  }
  .lp-hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3rem, 7vw, 5.5rem);
    font-weight: 900;
    line-height: 1.05;
    color: var(--dark);
    max-width: 780px;
    margin-bottom: 16px;
  }
  .lp-hero-title em {
    font-style: italic;
    color: var(--carnation);
    display: block;
    -webkit-text-stroke: 1.1px #d4af37;
    paint-order: stroke fill;
    text-shadow:
      0 0 2px rgba(255, 249, 251, 0.95),
      0 0 10px rgba(255, 249, 251, 0.8),
      0 4px 14px rgba(58, 47, 53, 0.24),
      0 0 1px rgba(212, 175, 55, 0.95),
      0 0 10px rgba(212, 175, 55, 0.28),
      1px -1px 0 rgba(255, 240, 190, 0.75),
      -1px 1px 0 rgba(255, 240, 190, 0.5);
  }
  .lp-hero-subtitle {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.25rem;
    font-style: italic;
    color: var(--mid);
    max-width: 520px;
    line-height: 1.6;
    margin-bottom: 40px;
  }
  .lp-cta-row { display: flex; gap: 14px; flex-wrap: wrap; justify-content: center; }
  .btn-hero-main {
    padding: 16px 40px;
    background: var(--carnation);
    border: none;
    border-radius: 50px;
    color: white;
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    box-shadow: 0 6px 24px rgba(241,95,97,0.4);
    transition: all 0.2s;
    letter-spacing: 0.5px;
  }
  .btn-hero-main:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(241,95,97,0.5); }
  .btn-hero-ghost {
    padding: 16px 40px;
    background: transparent;
    border: 2px solid var(--terra);
    border-radius: 50px;
    color: var(--terra);
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-hero-ghost:hover { background: var(--terra); color: white; }

  /* ── DIVIDER BANNER ── */
  .lp-banner {
    position: relative; z-index: 5;
    background: var(--terra);
    padding: 14px 0;
    overflow: hidden;
    white-space: nowrap;
  }
  .lp-banner-track {
    display: inline-flex;
    animation: marquee 22s linear infinite;
    gap: 0;
  }
  .lp-banner-item {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1rem;
    color: var(--peach);
    padding: 0 32px;
    letter-spacing: 0.5px;
  }
  .lp-banner-dot { color: var(--white); opacity: 0.6; }
  @keyframes marquee {
    from { transform: translateX(0); }
    to   { transform: translateX(-50%); }
  }

  /* ── FEATURES ── */
  .lp-features {
    position: relative; z-index: 5;
    padding: 72px 48px;
    max-width: 1100px;
    margin: 0 auto;
  }
  .lp-section-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--terra);
    text-align: center;
    margin-bottom: 10px;
  }
  .lp-section-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem;
    font-weight: 700;
    text-align: center;
    color: var(--dark);
    margin-bottom: 48px;
  }
  .lp-section-title em { font-style: italic; color: var(--carnation); }
  .lp-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
  }
  .lp-card {
    background: white;
    border: 2px solid var(--pink);
    border-radius: 20px;
    padding: 28px;
    position: relative;
    overflow: hidden;
    transition: all 0.25s;
  }
  .lp-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--terra), var(--carnation));
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s;
  }
  .lp-card:hover { border-color: var(--terra); transform: translateY(-4px); box-shadow: 0 12px 32px rgba(234,120,91,0.18); }
  .lp-card:hover::before { transform: scaleX(1); }
  .lp-card-icon {
    width: 48px; height: 48px;
    background: var(--pink);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--carnation);
    margin-bottom: 16px;
  }
  .lp-card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 8px;
  }
  .lp-card-desc {
    font-size: 0.875rem;
    color: var(--mid);
    line-height: 1.6;
  }

  /* ── TECH STRIP ── */
  .lp-tech {
    position: relative; z-index: 5;
    padding: 40px 48px 72px;
    text-align: center;
  }
  .lp-tech-label {
    font-size: 0.72rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 20px;
    opacity: 0.7;
  }
  .lp-tech-pills { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
  .lp-tech-pill {
    background: white;
    border: 1.5px solid var(--pink);
    border-radius: 50px;
    padding: 7px 18px;
    font-size: 0.82rem;
    color: var(--mid);
    font-weight: 500;
    letter-spacing: 0.5px;
  }

  /* ── FOOTER ── */
  .lp-footer {
    position: relative; z-index: 5;
    border-top: 1.5px solid rgba(234,120,91,0.2);
    text-align: center;
    padding: 24px;
    font-size: 0.8rem;
    color: var(--mid);
    opacity: 0.7;
    font-style: italic;
    font-family: 'Cormorant Garamond', serif;
  }
`;

const FashionPatternBg = () => (
  <svg className="lp-pattern" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400" preserveAspectRatio="xMidYMid slice">
    <defs>
      <pattern id="fashion" x="0" y="0" width="150" height="120" patternUnits="userSpaceOnUse" patternTransform="scale(0.95)">
        {/* Dress on hanger */}
        <g transform="translate(20,10)" fill="none" stroke="#EA785B" strokeWidth="1.3">
          <line x1="20" y1="0" x2="20" y2="8" />
          <path d="M10,8 Q20,4 30,8 L36,20 L4,20 Z" />
          <path d="M4,20 L0,55 L40,55 L36,20" />
          <path d="M0,55 Q20,65 40,55" />
        </g>
        {/* Scissors ornate */}
        <g transform="translate(90,15)" fill="none" stroke="#F15F61" strokeWidth="1.2">
          <line x1="0" y1="0" x2="30" y2="30" />
          <line x1="6" y1="0" x2="36" y2="30" />
          <circle cx="3" cy="3" r="5" />
          <circle cx="33" cy="3" r="5" />
          <path d="M30,30 Q35,38 28,42 Q22,44 25,36" />
          <path d="M36,30 Q42,38 36,44 Q30,46 28,38" />
        </g>
        {/* Mannequin */}
        <g transform="translate(160,5)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <line x1="15" y1="0" x2="15" y2="10" />
          <ellipse cx="15" cy="13" rx="6" ry="4" />
          <path d="M9,17 Q4,28 6,40 Q15,45 24,40 Q26,28 21,17" />
          <path d="M6,40 Q6,55 10,58 L20,58 Q24,55 24,40" />
          <line x1="15" y1="58" x2="15" y2="68" />
          <ellipse cx="15" cy="70" rx="8" ry="3" />
          {/* bow on mannequin */}
          <path d="M10,22 Q15,18 20,22 Q15,26 10,22Z" fill="#F15F61" stroke="none" opacity="0.6" />
        </g>
        {/* Thread spool */}
        <g transform="translate(210,30)" fill="none" stroke="#F0BBB4" strokeWidth="1.3">
          <ellipse cx="14" cy="5" rx="14" ry="4" />
          <rect x="0" y="5" width="28" height="22" rx="1" />
          <ellipse cx="14" cy="27" rx="14" ry="4" />
          <line x1="2" y1="9" x2="2" y2="23" />
          <line x1="26" y1="9" x2="26" y2="23" />
          {/* thread lines */}
          <line x1="6" y1="5" x2="6" y2="27" />
          <line x1="10" y1="5" x2="10" y2="27" />
          <line x1="14" y1="5" x2="14" y2="27" />
          <line x1="18" y1="5" x2="18" y2="27" />
          <line x1="22" y1="5" x2="22" y2="27" />
        </g>
        {/* Shoe heel */}
        <g transform="translate(70,80)" fill="none" stroke="#F15F61" strokeWidth="1.2">
          <path d="M5,20 Q0,15 0,8 Q0,0 12,0 Q22,0 24,8 L38,8 Q42,8 42,18 L5,20Z" />
          <line x1="38" y1="18" x2="38" y2="28" />
          <line x1="35" y1="28" x2="41" y2="28" />
          {/* dot details */}
          <circle cx="10" cy="6" r="2" fill="#F15F61" stroke="none" />
          <circle cx="18" cy="4" r="2" fill="#F15F61" stroke="none" />
          <circle cx="26" cy="4" r="2" fill="#F15F61" stroke="none" />
        </g>
        {/* Button 4-hole */}
        <g transform="translate(150,90)">
          <circle cx="14" cy="14" r="13" fill="none" stroke="#EA785B" strokeWidth="1.3" />
          <circle cx="10" cy="11" r="2" fill="#EA785B" />
          <circle cx="18" cy="11" r="2" fill="#EA785B" />
          <circle cx="10" cy="17" r="2" fill="#EA785B" />
          <circle cx="18" cy="17" r="2" fill="#EA785B" />
          <path d="M10,11 L18,17 M18,11 L10,17" stroke="#EA785B" strokeWidth="0.8" />
        </g>
        {/* Handbag */}
        <g transform="translate(195,85)" fill="none" stroke="#F0BBB4" strokeWidth="1.2">
          <path d="M5,20 Q0,20 0,30 L0,55 Q0,60 5,60 L45,60 Q50,60 50,55 L50,30 Q50,20 45,20Z" />
          <path d="M15,20 Q15,10 25,10 Q35,10 35,20" />
          <line x1="0" y1="35" x2="50" y2="35" />
          <rect x="20" y="30" width="10" height="10" rx="2" stroke="#EA785B" />
        </g>
        {/* Needle & thread wavy */}
        <g transform="translate(10,100)" fill="none" stroke="#F15F61" strokeWidth="1">
          <line x1="0" y1="0" x2="0" y2="50" />
          <ellipse cx="0" cy="4" rx="3" ry="5" />
          <path d="M0,50 Q12,40 10,28 Q8,16 0,20" />
        </g>
        {/* Bow ribbon */}
        <g transform="translate(35,130)" fill="none" stroke="#EA785B" strokeWidth="1.2">
          <path d="M20,10 Q5,0 0,10 Q5,18 20,10Z" />
          <path d="M20,10 Q35,0 40,10 Q35,18 20,10Z" />
          <circle cx="20" cy="10" r="4" fill="#EA785B" stroke="none" opacity="0.7" />
          <line x1="20" y1="14" x2="20" y2="30" />
          <path d="M20,30 Q14,36 16,40 M20,30 Q26,36 24,40" />
        </g>
        {/* Script text decoration */}
        <text x="90" y="140" fontFamily="serif" fontSize="9" fill="#EA785B" fontStyle="italic" opacity="0.7">Paris</text>
        <text x="160" y="155" fontFamily="serif" fontSize="7" fill="#F0BBB4" letterSpacing="2" opacity="0.8">✦ couture ✦</text>
        {/* Measuring tape */}
        <g transform="translate(10,160)" fill="none" stroke="#EA785B" strokeWidth="1.1">
          <rect x="0" y="4" width="80" height="10" rx="5" />
          {[5, 12, 19, 26, 33, 40, 47, 54, 61, 68, 75].map((x, i) => (
            <line key={i} x1={x} y1="4" x2={x} y2={i % 2 === 0 ? 14 : 12} stroke="#EA785B" />
          ))}
        </g>
        {/* Flowers small */}
        <g transform="translate(200,150)">
          <circle cx="20" cy="20" r="5" fill="none" stroke="#F0BBB4" strokeWidth="1" />
          {[0, 60, 120, 180, 240, 300].map((deg, i) => (
            <ellipse key={i} cx={20 + 9 * Math.cos(deg * Math.PI / 180)} cy={20 + 9 * Math.sin(deg * Math.PI / 180)} rx="4" ry="2.5" fill="none" stroke="#F15F61" strokeWidth="0.9"
              transform={`rotate(${deg} ${20 + 9 * Math.cos(deg * Math.PI / 180)} ${20 + 9 * Math.sin(deg * Math.PI / 180)})`} />
          ))}
        </g>
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#fashion)" />
  </svg>
);

const marqueeItems = [
  'Your Style, Elevated', '✦', 'ML-Powered Fashion', '✦',
  'Smart Wardrobe', '✦', 'Personal Stylist', '✦',
  'Your Style, Elevated', '✦', 'ML-Powered Fashion', '✦',
  'Smart Wardrobe', '✦', 'Personal Stylist', '✦',
];

const features = [
  { icon: <User className="w-5 h-5" />, title: "Body Shape Analysis", desc: "ML-powered body shape detection using pose estimation" },
  { icon: <Shirt className="w-5 h-5" />, title: "Smart Wardrobe", desc: "Automatically classify and organize your clothing items" },
  { icon: <Sparkles className="w-5 h-5" />, title: "Outfit Recommendations", desc: "Personalized outfit suggestions based on color harmony" },
  { icon: <ShoppingBag className="w-5 h-5" />, title: "Shopping Assistant", desc: "Check if new items match your existing wardrobe" },
  { icon: <Trash2 className="w-5 h-5" />, title: "Discard Suggestions", desc: "Find items that don't suit your style profile" },
];

function LandingPage() {
  const navigate = useNavigate();

  return (
    <>
      <style>{css}</style>
      <div className="lp-body">
        {/* NAV */}
        <nav className="lp-nav">
          <div className="lp-logo">Fit<span>Me</span></div>
          <div className="lp-nav-btns">
            <button className="btn-ghost" onClick={() => navigate('/login')}>Sign In</button>
            <button className="btn-fill" onClick={() => navigate('/onboarding')}>Get Started</button>
          </div>
        </nav>

        {/* HERO */}
        <section className="lp-hero">
          <div className="lp-hero-badge">
            <Sparkles size={12} /> ML-Powered Personal Stylist
          </div>
          <h1 className="lp-hero-title">
            Dress with
            <em>Confidence</em>
          </h1>
          <p className="lp-hero-subtitle">
            Your intelligent fashion companion — analyzing your body shape, skin tone, and wardrobe to curate outfits made just for you.
          </p>
          <div className="lp-cta-row">
            <button className="btn-hero-main" onClick={() => navigate('/onboarding')}>
              Build My Style Profile →
            </button>
            <button className="btn-hero-ghost" onClick={() => navigate('/login')}>
              I have an account
            </button>
          </div>
        </section>

        {/* MARQUEE BANNER */}
        <div className="lp-banner">
          <div className="lp-banner-track">
            {[...marqueeItems, ...marqueeItems].map((item, i) => (
              <span key={i} className="lp-banner-item">{item}</span>
            ))}
          </div>
        </div>

        {/* FEATURES */}
        <section className="lp-features">
          <p className="lp-section-label">What we offer</p>
          <h2 className="lp-section-title">Everything your wardrobe <em>deserves</em></h2>
          <div className="lp-grid">
            {features.map((f, i) => (
              <div className="lp-card" key={i}>
                <div className="lp-card-icon">{f.icon}</div>
                <div className="lp-card-title">{f.title}</div>
                <div className="lp-card-desc">{f.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* TECH */}
        <div className="lp-tech">
          <p className="lp-tech-label">Built with</p>
          <div className="lp-tech-pills">
            {['YOLOv8', 'OpenCV', 'FastAPI', 'React', 'Tailwind CSS', 'SQLAlchemy'].map(t => (
              <span className="lp-tech-pill" key={t}>{t}</span>
            ))}
          </div>
        </div>

        <footer className="lp-footer">
          Made with ♥ for fashion lovers everywhere · FitMe © 2025
        </footer>
      </div>
    </>
  );
}

export default LandingPage;