// Shared design tokens & base styles injected into every inner page
export const sharedCSS = `
  :root {
    --terra:    #B08A56;
    --white:    #FFF9FB;
    --pink:     #E9C7D2;
    --carnation:#DFA7BB;
    --peach:    #F4EFEF;
    --dark:     #3A2F35;
    --mid:      #6D5863;
    --deep:     #5A4751;
    --mauve:    #B88FA4;
    --bg-base:  #F4EFEF;
    --wallpaper-url: url('/patterns/bows.jpg');
  }

  /* ── page shell ── */
  .pg {
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    background-color: var(--bg-base);
    background-image:
      linear-gradient(140deg, rgba(255,249,251,0.8), rgba(244,239,239,0.78)),
      var(--wallpaper-url);
    background-size: 100% 100%, 340px auto;
    background-repeat: no-repeat, repeat;
    background-attachment: fixed, fixed;
    color: var(--dark);
  }

  /* ── top nav bar ── */
  .pg-nav {
    background: rgba(255,249,251,0.9);
    backdrop-filter: blur(10px);
    border-bottom: 1.5px solid rgba(184,143,164,0.28);
    padding: 0 32px;
    height: 62px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 50;
  }
  .pg-nav-left { display:flex; align-items:center; gap:14px; }
  .pg-back {
    display: inline-flex; align-items: center; gap:5px;
    background: white;
    border: 1.5px solid var(--pink);
    border-radius: 50px;
    padding: 6px 14px;
    font-size: 0.78rem;
    font-family: 'DM Sans', sans-serif;
    color: var(--mid);
    cursor: pointer;
    transition: all .18s;
  }
  .pg-back:hover { border-color: var(--terra); color: var(--terra); }
  .pg-title {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.25rem;
    color: var(--dark);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .pg-title-icon { color: var(--carnation); }
  .pg-logo {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.5rem;
    color: var(--terra);
    text-decoration: none;
  }

  /* ── content wrapper ── */
  .pg-body {
    max-width: 1100px;
    margin: 0 auto;
    padding: 36px 24px 80px;
  }
  .pg-body-narrow {
    max-width: 760px;
    margin: 0 auto;
    padding: 36px 24px 80px;
  }

  /* ── stat/summary cards ── */
  .stat-row { display:grid; gap:16px; margin-bottom:28px; }
  .stat-card {
    background: white;
    border: 2px solid var(--pink);
    border-radius: 18px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
  }
  .stat-card::before {
    content:'';
    position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, var(--terra), var(--carnation));
  }
  .stat-label {
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 6px;
  }
  .stat-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--dark);
    line-height: 1;
  }
  .stat-value.sm { font-size: 1.4rem; }
  .stat-accent { color: var(--carnation); }
  .stat-green  { color: #4a7c59; }
  .stat-orange { color: var(--terra); }

  /* ── section headings ── */
  .sec-head {
    display: flex; align-items: center; gap:8px;
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 16px;
  }
  .sec-head-icon { color: var(--carnation); }

  /* ── white content card ── */
  .wcard {
    background: white;
    border: 2px solid var(--pink);
    border-radius: 22px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(234,120,91,0.06);
  }
  .wcard-pad { padding: 28px; }
  .wcard-head {
    background: var(--terra);
    padding: 22px 28px;
    position: relative;
  }
  .wcard-head::after {
    content:'';
    position:absolute; bottom:-1px; left:0; right:0;
    height:28px; background:white;
    clip-path: ellipse(55% 100% at 50% 100%);
  }
  .wcard-head-title {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.5rem;
    color: white;
  }
  .wcard-head-sub { font-size: 0.75rem; color: var(--peach); margin-top:3px; }

  /* ── shopping hero header override ── */
  .shop-hero-head {
    background: linear-gradient(135deg, rgba(223,167,187,0.88), rgba(184,143,164,0.82));
  }
  .shop-hero-head .wcard-head-title { color: #FFF9FB; }
  .shop-hero-head .wcard-head-sub {
    color: rgba(255,249,251,0.92);
    font-size: 0.82rem;
  }

  /* ── sessions hero header override ── */
  .sessions-hero-head {
    background: linear-gradient(135deg, rgba(233,199,210,0.9), rgba(184,143,164,0.78));
    padding: 24px 28px;
  }
  .sessions-hero-head .wcard-head-title {
    color: #FFF9FB;
    font-size: 1.68rem;
    letter-spacing: 0.2px;
  }
  .sessions-hero-sub {
    color: rgba(255,249,251,0.95);
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 1.08rem;
    font-weight: 500;
    letter-spacing: 0.15px;
    line-height: 1.24;
    margin-top: 4px;
  }

  /* ── form fields ── */
  .ff { margin-bottom:14px; }
  .ff label {
    display:block;
    font-size: 0.68rem;
    letter-spacing:1.5px;
    text-transform:uppercase;
    color: var(--mid);
    font-weight:500;
    margin-bottom:5px;
  }
  .ff input, .ff select {
    width:100%;
    padding: 11px 15px;
    border: 2px solid var(--pink);
    border-radius:13px;
    background: rgba(255,190,152,0.07);
    font-family:'DM Sans',sans-serif;
    font-size:0.88rem;
    color:var(--dark);
    outline:none;
    transition: all .18s;
    appearance: none;
  }
  .ff input:focus, .ff select:focus {
    border-color: var(--terra);
    box-shadow: 0 0 0 3px rgba(234,120,91,0.14);
    background: rgba(255,190,152,0.14);
  }
  .ff input::placeholder { color:#C4A090; }

  /* ── buttons ── */
  .btn-p {
    padding: 11px 24px;
    background: var(--carnation);
    border: none; border-radius:50px;
    color:white; font-family:'DM Sans',sans-serif;
    font-size:0.88rem; font-weight:500;
    cursor:pointer; letter-spacing:.4px;
    box-shadow: 0 4px 14px rgba(241,95,97,.32);
    transition: all .18s;
    display:inline-flex; align-items:center; gap:6px;
  }
  .btn-p:hover:not(:disabled) { transform:translateY(-2px); box-shadow:0 7px 20px rgba(241,95,97,.42); }
  .btn-p:disabled { opacity:.45; cursor:not-allowed; }
  .btn-p.full { width:100%; justify-content:center; }

  .btn-s {
    padding: 11px 24px;
    background: white;
    border: 2px solid var(--pink); border-radius:50px;
    color:var(--mid); font-family:'DM Sans',sans-serif;
    font-size:0.88rem; font-weight:500;
    cursor:pointer; letter-spacing:.4px;
    transition: all .18s;
    display:inline-flex; align-items:center; gap:6px;
  }
  .btn-s:hover:not(:disabled) { border-color:var(--terra); color:var(--terra); }
  .btn-s:disabled { opacity:.45; cursor:not-allowed; }
  .btn-s.full { width:100%; justify-content:center; }

  .btn-danger {
    padding: 9px 20px;
    background: #fee2e2;
    border: 1.5px solid #fca5a5; border-radius:50px;
    color:#b91c1c; font-family:'DM Sans',sans-serif;
    font-size:0.82rem; font-weight:500;
    cursor:pointer;
    transition: all .18s;
    display:inline-flex; align-items:center; gap:5px;
  }
  .btn-danger:hover:not(:disabled) { background:#fecaca; border-color:#f87171; }
  .btn-danger:disabled { opacity:.45; cursor:not-allowed; }

  .btn-warn {
    padding: 9px 20px;
    background: rgba(255,190,152,0.25);
    border: 1.5px solid var(--peach); border-radius:50px;
    color:var(--terra); font-family:'DM Sans',sans-serif;
    font-size:0.82rem; font-weight:500;
    cursor:pointer;
    transition: all .18s;
    display:inline-flex; align-items:center; gap:5px;
  }
  .btn-warn:hover:not(:disabled) { background:rgba(255,190,152,0.45); border-color:var(--terra); }

  .btn-row { display:flex; gap:10px; margin-top:16px; flex-wrap:wrap; }

  /* ── alerts ── */
  .alert-e {
    background:rgba(241,95,97,0.08); border:1.5px solid var(--carnation);
    border-radius:12px; padding:10px 14px;
    font-size:0.83rem; color:var(--carnation); margin-bottom:16px;
  }
  .alert-s {
    background:rgba(74,124,89,0.08); border:1.5px solid #4a7c59;
    border-radius:12px; padding:10px 14px;
    font-size:0.83rem; color:#4a7c59; margin-bottom:16px;
  }
  .alert-w {
    background:rgba(255,190,152,0.25); border:1.5px solid var(--peach);
    border-radius:12px; padding:14px 16px;
    font-size:0.85rem; color:var(--terra); margin-bottom:16px;
  }

  /* ── score bar ── */
  .score-bar-wrap { margin-bottom:14px; }
  .score-bar-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:5px; }
  .score-bar-label { font-size:0.82rem; color:var(--mid); font-weight:500; }
  .score-bar-detail { font-size:0.75rem; color:#C4A090; }
  .score-bar-track { height:7px; background:var(--pink); border-radius:10px; }
  .score-bar-fill { height:7px; border-radius:10px; transition:width .5s; }
  .score-bar-fill.green  { background:linear-gradient(90deg,#4a7c59,#6faf88); }
  .score-bar-fill.yellow { background:linear-gradient(90deg,var(--terra),var(--peach)); }
  .score-bar-fill.red    { background:linear-gradient(90deg,var(--carnation),#f87171); }
  .score-bar-pct { font-size:0.72rem; font-weight:600; color:var(--mid); text-align:right; margin-top:3px; }

  /* ── spinner loader ── */
  .loader-wrap {
    min-height:100vh; background:var(--white);
    display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:16px;
  }
  .loader-ring {
    width:52px; height:52px;
    border:3px solid var(--pink);
    border-top-color:var(--carnation);
    border-radius:50%;
    animation:spin .8s linear infinite;
  }
  @keyframes spin { to { transform:rotate(360deg); } }
  .loader-text {
    font-family:'Cormorant Garamond',serif;
    font-style:italic;
    font-size:1.1rem;
    color:var(--mid);
  }

  /* ── upload zone ── */
  .upload-zone {
    border: 2px dashed var(--pink);
    border-radius:18px; padding:40px 24px;
    text-align:center; cursor:pointer;
    transition:all .2s;
    background:rgba(255,190,152,0.05);
  }
  .upload-zone:hover { border-color:var(--terra); background:rgba(255,190,152,0.12); }
  .upload-zone img { max-height:220px; border-radius:12px; margin:0 auto; display:block; }

  /* ── grid helpers ── */
  .g2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  .g3 { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
  .g4 { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  @media(max-width:640px) {
    .g2,.g3,.g4 { grid-template-columns:1fr 1fr; }
    .g4 { grid-template-columns:1fr 1fr; }
  }

  /* ── pill badge ── */
  .pill {
    display:inline-flex; align-items:center; gap:4px;
    padding:3px 10px; border-radius:50px; font-size:0.7rem; font-weight:500;
  }
  .pill-green { background:rgba(74,124,89,0.12); color:#4a7c59; border:1px solid rgba(74,124,89,0.25); }
  .pill-orange { background:rgba(234,120,91,0.12); color:var(--terra); border:1px solid rgba(234,120,91,0.3); }
  .pill-pink { background:rgba(241,95,97,0.1); color:var(--carnation); border:1px solid rgba(241,95,97,0.25); }
  .pill-gray { background:#f3f4f6; color:#6b7280; border:1px solid #e5e7eb; }
  .pill-peach { background:rgba(255,190,152,0.25); color:var(--terra); border:1px solid var(--peach); }

  /* ── modal overlay ── */
  .modal-bg {
    position:fixed; inset:0;
    background:rgba(61,43,43,0.55);
    backdrop-filter:blur(4px);
    display:flex; align-items:center; justify-content:center;
    padding:16px; z-index:100;
  }
  .modal-box {
    background:white;
    border-radius:24px;
    border:2.5px solid var(--mauve);
    box-shadow: 6px 8px 0 var(--mauve);
    width:100%; max-width:480px;
    max-height:90vh; overflow-y:auto;
  }
  .modal-head {
    background:
      radial-gradient(circle at 20px 16px, rgba(255, 245, 214, 0.95) 0 1.6px, transparent 1.8px),
      radial-gradient(circle at 28px 24px, rgba(255, 245, 214, 0.75) 0 1px, transparent 1.2px),
      radial-gradient(circle at calc(100% - 20px) 16px, rgba(255, 245, 214, 0.95) 0 1.6px, transparent 1.8px),
      radial-gradient(circle at calc(100% - 28px) 24px, rgba(255, 245, 214, 0.75) 0 1px, transparent 1.2px),
      linear-gradient(180deg, #caa1b4 0%, #b88fa4 100%);
    padding:20px 24px 36px;
    position:relative;
  }
  .modal-head::after {
    content:''; position:absolute;
    bottom:-1px; left:0; right:0;
    height:26px; background:white;
    clip-path:ellipse(56% 100% at 50% 100%);
  }
  .modal-head-title {
    font-family:'Playfair Display',serif;
    font-style:italic; font-size:1.3rem; color:white;
  }
  .modal-body { padding:20px 24px 28px; }

  /* ── clothing item card ── */
  .cloth-card {
    background:white; border:2px solid var(--pink);
    border-radius:18px; overflow:hidden;
    transition:all .22s; cursor:default;
  }
  .cloth-card:hover { border-color:var(--terra); box-shadow:0 6px 22px rgba(234,120,91,0.16); transform:translateY(-3px); }
  .cloth-card-img {
    aspect-ratio:1; background:var(--white);
    display:flex; align-items:center; justify-content:center;
    position:relative; overflow:hidden;
  }
  .cloth-card-img img { width:100%; height:100%; object-fit:cover; }
  .cloth-card-img .placeholder { font-size:3rem; }
  .cloth-card-body { padding:12px 14px; }
  .cloth-card-title { font-size:0.85rem; font-weight:500; color:var(--dark); text-transform:capitalize; }
  .cloth-card-sub { font-size:0.72rem; color:#C4A090; text-transform:capitalize; margin-top:2px; }
  .cloth-card-pills { display:flex; gap:5px; flex-wrap:wrap; margin-top:7px; }
  .cloth-del-btn {
    position:absolute; top:8px; right:8px;
    background:var(--carnation); border:none; border-radius:10px;
    padding:6px; color:white; cursor:pointer;
    opacity:0; transition:opacity .18s;
  }
  .cloth-card:hover .cloth-del-btn { opacity:1; }

  /* ── discard / keep item card ── */
  .discard-card {
    background:white; border:2px solid var(--pink);
    border-radius:20px; overflow:hidden;
    display:flex; transition:border-color .2s;
  }
  .discard-card.kept { border-color:#4a7c59; }
  .discard-card-img {
    width:110px; min-height:110px; flex-shrink:0;
    background:var(--white);
    display:flex; align-items:center; justify-content:center;
    font-size:3rem;
  }
  .discard-card-img img { width:100%; height:100%; object-fit:cover; }
  .discard-card-body { flex:1; padding:16px 18px; }
  .discard-card-title { font-family:'Playfair Display',serif; font-size:1rem; font-weight:700; color:var(--dark); text-transform:capitalize; }
  .discard-card-sub { font-size:0.72rem; color:#C4A090; text-transform:capitalize; margin-top:2px; }
  .discard-card-reasons { margin-top:8px; }
  .discard-reason { font-size:0.78rem; color:var(--terra); display:flex; align-items:flex-start; gap:5px; margin-bottom:4px; }
  .tips-box {
    margin-top:14px; background:rgba(240,187,180,0.2);
    border:1.5px solid var(--pink); border-radius:14px; padding:14px;
  }
  .tips-box-title { font-size:0.75rem; font-weight:500; color:var(--mid); margin-bottom:8px; display:flex; align-items:center; gap:5px; letter-spacing:.5px; }
  .tips-list { list-style:none; padding:0; margin:0; }
  .tips-list li { font-size:0.78rem; color:var(--mid); display:flex; gap:6px; margin-bottom:6px; }

  /* ── outfit card ── */
  .outfit-card {
    background:white; border:2px solid var(--pink);
    border-radius:22px; overflow:hidden; margin-bottom:20px;
    box-shadow:0 2px 16px rgba(234,120,91,0.06);
    transition:box-shadow .22s;
  }
  .outfit-card:hover { box-shadow:0 8px 32px rgba(234,120,91,0.15); }
  .outfit-card-head {
    background:linear-gradient(135deg, rgba(223,167,187,0.34), rgba(233,199,210,0.45));
    border-bottom:1.5px solid rgba(184,143,164,0.35);
    padding:20px 26px;
    display:flex; align-items:center; justify-content:space-between;
  }
  .outfit-card-num {
    font-family:'Playfair Display',serif;
    font-style:italic; font-size:1.4rem; color:var(--deep);
  }
  .outfit-card-score-badge {
    background:rgba(255,249,251,0.9); border-radius:50px;
    border:1.5px solid rgba(184,143,164,0.35);
    padding:6px 14px;
    font-size:0.82rem; font-weight:600;
    color:var(--deep);
  }
  .outfit-card-body { padding:22px 26px; }
  .outfit-scores { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:20px; }
  .outfit-score-item { text-align:center; }
  .outfit-score-icon { color:var(--pink); margin-bottom:5px; display:flex; justify-content:center; }
  .outfit-score-label { font-size:0.65rem; letter-spacing:1px; text-transform:uppercase; color:var(--mid); margin-bottom:6px; }

  /* ── sessions ── */
  .session-card {
    background:white; border:2px solid var(--pink);
    border-radius:20px; padding:20px 22px;
    display:flex; flex-direction:column; gap:10px;
    transition:border-color .2s;
  }
  .session-card.active-s { border-color:rgba(74,124,89,0.4); }
  .session-ua { font-size:0.88rem; font-weight:500; color:var(--dark); display:flex; align-items:center; gap:7px; }
  .session-meta { font-size:0.75rem; color:var(--mid); display:grid; grid-template-columns:1fr 1fr; gap:4px 14px; }
  .session-meta span { display:flex; align-items:center; gap:4px; }

  /* ── shopping rec banner ── */
  .rec-banner {
    border-radius:22px; padding:28px;
    display:flex; align-items:center; gap:18px;
    margin-bottom:22px;
  }
  .rec-banner.buy { background:rgba(74,124,89,0.1); border:2.5px solid rgba(74,124,89,0.4); }
  .rec-banner.skip { background:rgba(241,95,97,0.08); border:2.5px solid rgba(241,95,97,0.35); }
  .rec-banner.consider { background:rgba(255,190,152,0.25); border:2.5px solid var(--peach); }
  .rec-banner-icon { font-size:2.8rem; }
  .rec-banner-title {
    font-family:'Playfair Display',serif;
    font-size:1.6rem; font-weight:700; text-transform:uppercase;
  }
  .rec-banner.buy .rec-banner-title { color:#4a7c59; }
  .rec-banner.skip .rec-banner-title { color:var(--carnation); }
  .rec-banner.consider .rec-banner-title { color:var(--terra); }
  .rec-banner-sub { font-size:0.82rem; color:var(--mid); margin-top:3px; font-style:italic; font-family:'Cormorant Garamond',serif; }
`;
