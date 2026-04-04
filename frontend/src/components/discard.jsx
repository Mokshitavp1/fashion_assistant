import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDiscardRecommendations } from '../services/api';
import { ArrowLeft, Trash2, Heart, Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react';
import { sharedCSS } from './sharedStyles';

const IMAGE_BASE_URL = 'http://127.0.0.1:8000';

function resolveItemImageUrl(item) {
  const token = localStorage.getItem('accessToken');
  const withToken = (url) => {
    if (!url || !token || !url.includes('/images/')) return url;
    return `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`;
  };

  const toEncryptedImageUrl = (idLike) => {
    if (!idLike) return null;
    const cleanId = String(idLike).replace(/^encrypted:\/\//, '');
    if (!cleanId) return null;
    return withToken(`${IMAGE_BASE_URL}/images/${encodeURIComponent(cleanId)}`);
  };

  if (item?.image_url) {
    const abs = item.image_url.startsWith('http')
      ? item.image_url
      : `${IMAGE_BASE_URL}${item.image_url.startsWith('/') ? '' : '/'}${item.image_url}`;
    return withToken(abs);
  }

  if (item?.image_id) {
    return toEncryptedImageUrl(item.image_id);
  }

  if (!item?.image_path) return null;
  const raw = String(item.image_path);

  if (raw.startsWith('encrypted://')) {
    return toEncryptedImageUrl(raw);
  }

  if (raw.startsWith('http')) return withToken(raw);
  if (raw.includes('/') || raw.includes('\\')) {
    const fn = raw.replace(/\\/g, '/').split('/').pop();
    return `${IMAGE_BASE_URL}/uploads/${fn}`;
  }
  return toEncryptedImageUrl(raw);
}

const STYLING_TIPS = {
  undertone_mismatch: {
    warm_item_cool_undertone: [
      "Pair this with cool-toned accessories to balance the warmth",
      "Layer it under a cool-toned jacket or cardigan",
      "Add a scarf in a cool neutral shade to blend the tones",
      "Use it as an accent piece with mostly cool-toned outfits",
    ],
    cool_item_warm_undertone: [
      "Wear it with warm-toned accessories like gold jewelry",
      "Pair with warm neutrals like beige or camel",
      "Layer over a warm-toned inner piece to soften the contrast",
      "Add a warm belt or bag to balance the cool tones",
    ],
  },
  body_shape: {
    inverted_triangle: [
      "Balance with wider bottoms like bootcut jeans or A-line skirts",
      "Add volume to the lower body with layered skirts",
      "Use V-necks to elongate and slim the upper body",
    ],
    pear: [
      "Draw attention to the upper body with bold tops or jewelry",
      "Use A-line skirts or wide-leg pants to balance proportions",
      "Wear lighter colors on top and darker on bottom",
    ],
    rectangle: [
      "Create curves with belts at the waist",
      "Use peplum tops or wrap dresses to define the waist",
      "Choose bootcut or flared pants to add shape",
    ],
    hourglass: [
      "Emphasize the waist with fitted tops and high-waisted bottoms",
      "Wear wrap dresses to highlight curves",
      "Use pencil skirts to showcase your balanced proportions",
    ],
    apple: [
      "Draw attention to legs with statement shoes",
      "Use empire-waist tops to create a flattering silhouette",
      "Choose V-neck tops to elongate the torso",
    ],
  },
  low_versatility: [
    "Style it as a statement piece with simple, neutral basics",
    "Use it for specific occasions like casual weekends",
    "Pair with versatile basics like black jeans or white shirts",
  ],
};

const randomTips = (tips, n = 2) => [...tips].sort(() => Math.random() - .5).slice(0, n);

function Discard() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [kept, setKept] = useState({});

  const fetchData = useCallback(async () => {
    try {
      const r = await getDiscardRecommendations(userId);
      setData(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to fetch recommendations');
    } finally { setLoading(false); }
  }, [userId]);

  useEffect(() => {
    if (!userId) { navigate('/onboarding'); return; }
    fetchData();
  }, [fetchData, userId, navigate]);

  if (loading) return (
    <><style>{sharedCSS}</style>
      <div className="loader-wrap"><div className="loader-ring" />
        <p className="loader-text">Analysing your wardrobe…</p>
      </div>
    </>
  );

  if (error) return (
    <><style>{sharedCSS}</style>
      <div className="pg">
        <nav className="pg-nav">
          <button className="pg-back" onClick={() => navigate('/wardrobe')}><ArrowLeft size={13} /> Wardrobe</button>
        </nav>
        <div className="pg-body-narrow" style={{ textAlign: 'center', paddingTop: 80 }}>
          <div className="wcard wcard-pad">
            <AlertTriangle size={40} style={{ color: 'var(--terra)', margin: '0 auto 16px' }} />
            <div style={{ fontFamily: 'Playfair Display,serif', fontSize: '1.3rem', marginBottom: 8 }}>Unable to Analyse</div>
            <p style={{ color: 'var(--mid)', marginBottom: 20 }}>{error}</p>
            <button className="btn-p" onClick={() => navigate('/wardrobe')}>Go to Wardrobe</button>
          </div>
        </div>
      </div>
    </>
  );

  const analysis = data?.analysis;
  const discardItems = analysis?.items_to_discard || [];
  const keepItems = analysis?.items_to_keep || [];

  return (
    <>
      <style>{sharedCSS}</style>
      <div className="pg">
        <nav className="pg-nav">
          <div className="pg-nav-left">
            <button className="pg-back" onClick={() => navigate('/wardrobe')}><ArrowLeft size={13} /> Wardrobe</button>
            <span className="pg-title"><span className="pg-title-icon"><AlertTriangle size={16} /></span> Wardrobe Analysis</span>
          </div>
        </nav>

        <div className="pg-body-narrow">
          {/* Summary stats */}
          <div className="g3 stat-row">
            <div className="stat-card">
              <div className="stat-label">Total Items</div>
              <div className="stat-value">{analysis?.total_items}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Keep</div>
              <div className="stat-value stat-green">{analysis?.keep_count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Review</div>
              <div className="stat-value stat-orange">{analysis?.discard_count}</div>
            </div>
          </div>

          {/* Items to review */}
          {discardItems.length > 0 && (
            <div style={{ marginBottom: 32 }}>
              <div className="sec-head">
                <AlertTriangle size={17} className="sec-head-icon" /> Items to Review
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {discardItems.map(item => (
                  <DiscardCard
                    key={item.item_id}
                    item={item}
                    bodyShape={data?.body_shape}
                    isKept={!!kept[item.item_id]}
                    onKeep={() => setKept(p => ({ ...p, [item.item_id]: true }))}
                    onUndo={() => setKept(p => { const n = { ...p }; delete n[item.item_id]; return n; })}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Items to keep */}
          {keepItems.length > 0 && (
            <div>
              <div className="sec-head">
                <CheckCircle size={17} className="sec-head-icon" /> Great Pieces — Keep These!
              </div>
              <div className="g3">
                {keepItems.map(item => <KeepCard key={item.item_id} item={item} />)}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function DiscardCard({ item, bodyShape, isKept, onKeep, onUndo }) {
  const [showTips, setShowTips] = useState(false);
  const [imgErr, setImgErr] = useState(false);

  const getTips = () => {
    let tips = [];
    if (item.reasons.some(r => r.includes('Warm color clashes with cool')))
      tips.push(...randomTips(STYLING_TIPS.undertone_mismatch.warm_item_cool_undertone));
    if (item.reasons.some(r => r.includes('Cool color clashes with warm')))
      tips.push(...randomTips(STYLING_TIPS.undertone_mismatch.cool_item_warm_undertone));
    if (bodyShape && STYLING_TIPS.body_shape[bodyShape])
      tips.push(...randomTips(STYLING_TIPS.body_shape[bodyShape]));
    if (item.reasons.some(r => r.includes('versatility')))
      tips.push(...randomTips(STYLING_TIPS.low_versatility));
    if (tips.length === 0)
      tips = ["Try pairing with neutral basics to make it work", "Use it as a layering piece for a more versatile look"];
    return tips.slice(0, 3);
  };

  const imgUrl = resolveItemImageUrl(item);

  return (
    <div className={`discard-card ${isKept ? 'kept' : ''}`}>
      <div className="discard-card-img">
        {imgUrl && !imgErr
          ? <img src={imgUrl} alt="clothing" onError={() => setImgErr(true)} />
          : <span>👗</span>
        }
      </div>
      <div className="discard-card-body">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
          <div>
            <div className="discard-card-title">{item.item_color} {item.item_type}</div>
            <div className="discard-card-sub">{item.item_category}</div>
          </div>
          <span className={`pill ${item.overall_score >= 0.5 ? 'pill-peach' : 'pill-pink'}`}>
            {(item.overall_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="discard-card-reasons">
          {item.reasons.map((r, i) => (
            <div className="discard-reason" key={i}><span>⚠</span> {r}</div>
          ))}
        </div>
        <div className="btn-row">
          {!isKept ? (
            <>
              <button className="btn-s" style={{ padding: '7px 14px', fontSize: '0.78rem' }} onClick={onKeep}>
                <Heart size={13} /> Keep It
              </button>
              <button className="btn-s" style={{ padding: '7px 14px', fontSize: '0.78rem' }} onClick={() => setShowTips(v => !v)}>
                <Lightbulb size={13} /> How to Style
              </button>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: '0.82rem', color: '#4a7c59', display: 'flex', alignItems: 'center', gap: 5 }}>
                <Heart size={13} style={{ fill: '#4a7c59' }} /> Keeping this!
              </span>
              <button onClick={onUndo} style={{ background: 'none', border: 'none', fontSize: '0.75rem', color: 'var(--mid)', textDecoration: 'underline', cursor: 'pointer', fontFamily: 'DM Sans,sans-serif' }}>Undo</button>
            </div>
          )}
        </div>
        {showTips && !isKept && (
          <div className="tips-box">
            <div className="tips-box-title"><Lightbulb size={13} /> Styling Tips</div>
            <ul className="tips-list">
              {getTips().map((t, i) => <li key={i}><span>✦</span>{t}</li>)}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function KeepCard({ item }) {
  const [imgErr, setImgErr] = useState(false);
  const imgUrl = resolveItemImageUrl(item);
  return (
    <div className="cloth-card">
      <div className="cloth-card-img">
        {imgUrl && !imgErr
          ? <img src={imgUrl} alt="clothing" onError={() => setImgErr(true)} />
          : <span className="placeholder">👗</span>
        }
      </div>
      <div className="cloth-card-body">
        <div className="cloth-card-title">{item.item_color} {item.item_type}</div>
        <div className="cloth-card-sub">{item.item_category}</div>
        <div className="cloth-card-pills">
          <span className="pill pill-green">{(item.overall_score * 100).toFixed(0)}% match</span>
        </div>
      </div>
    </div>
  );
}

export default Discard;