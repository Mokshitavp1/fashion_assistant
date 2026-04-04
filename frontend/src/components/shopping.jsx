import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeShoppingItem } from '../services/api';
import { ArrowLeft, Camera, Upload, ShoppingBag, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { sharedCSS } from './sharedStyles';

function Shopping() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImg = (e) => {
    const f = e.target.files[0];
    if (f) { setImage(f); setPreview(URL.createObjectURL(f)); setAnalysis(null); }
  };

  const handleAnalyze = async () => {
    if (!image) { alert('Please select an image'); return; }
    setLoading(true);
    try {
      const r = await analyzeShoppingItem(userId, image);
      setAnalysis(r.data.analysis);
    } catch (e) { alert(e.response?.data?.detail || 'Failed to analyse item'); }
    finally { setLoading(false); }
  };

  const recMeta = {
    buy: { cls: 'buy', emoji: '✅', label: 'Buy It!', sub: 'This piece works beautifully with your wardrobe.' },
    skip: { cls: 'skip', emoji: '✗', label: 'Skip It', sub: 'This item may not work well for your style profile.' },
    consider: { cls: 'consider', emoji: '💡', label: 'Consider', sub: 'This could work — with the right styling.' },
  };
  const rec = analysis ? (recMeta[analysis.recommendation] || recMeta.consider) : null;

  return (
    <>
      <style>{sharedCSS}</style>
      <div className="pg">
        <nav className="pg-nav">
          <div className="pg-nav-left">
            <button className="pg-back" onClick={() => navigate('/dashboard')}><ArrowLeft size={13} /> Dashboard</button>
            <span className="pg-title"><ShoppingBag size={15} className="pg-title-icon" /> Shopping Assistant</span>
          </div>
        </nav>

        <div className="pg-body-narrow">
          {!analysis ? (
            /* Upload panel */
            <div className="wcard">
              <div className="wcard-head shop-hero-head">
                <div className="wcard-head-title">Considering a Purchase?</div>
                <div className="wcard-head-sub">Upload a photo and we&apos;ll tell you how well it fits your wardrobe and personal style.</div>
              </div>
              <div className="wcard-pad" style={{ paddingTop: 36 }}>
                <div className="ff">
                  <label>Item Photo</label>
                  <div className="upload-zone">
                    <input type="file" accept="image/*" onChange={handleImg} style={{ display: 'none' }} id="shop-up" />
                    <label htmlFor="shop-up" style={{ cursor: 'pointer', display: 'block' }}>
                      {preview
                        ? <img src={preview} alt="preview" />
                        : <>
                          <Camera size={40} style={{ margin: '0 auto 12px', display: 'block', color: 'var(--pink)' }} />
                          <div style={{ fontSize: '0.9rem', color: 'var(--mid)', fontWeight: 500 }}>Click to upload a photo</div>
                          <div style={{ fontSize: '0.75rem', color: '#C4A090', marginTop: 4 }}>PNG, JPG up to 10MB</div>
                        </>
                      }
                    </label>
                  </div>
                </div>
                {preview && (
                  <div className="btn-row">
                    <button className="btn-s full" onClick={() => { setImage(null); setPreview(''); }}>Change Photo</button>
                    <button className="btn-p full" onClick={handleAnalyze} disabled={loading}>
                      {loading ? 'Analysing…' : 'Analyse Item →'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Results */
            <div>
              {/* Rec banner */}
              <div className={`rec-banner ${rec.cls}`}>
                <div className="rec-banner-icon">{rec.emoji}</div>
                <div>
                  <div className="rec-banner-title">{rec.label}</div>
                  <div className="rec-banner-sub">{rec.sub}</div>
                </div>
              </div>

              {/* Item details */}
              <div className="wcard" style={{ marginBottom: 16 }}>
                <div className="wcard-pad">
                  <div className="sec-head" style={{ fontSize: '0.95rem', marginBottom: 14 }}><span className="sec-head-icon">✦</span> Item Details</div>
                  <div className="g4" style={{ gap: 10 }}>
                    {[
                      ['Type', analysis.item_classification.type],
                      ['Category', analysis.item_classification.category],
                      ['Color', analysis.item_classification.color_primary],
                      ['Pattern', analysis.item_classification.pattern],
                    ].map(([k, v]) => (
                      <div key={k} style={{ background: 'var(--white)', borderRadius: 12, padding: '10px 12px' }}>
                        <div style={{ fontSize: '0.62rem', letterSpacing: '1.2px', textTransform: 'uppercase', color: '#C4A090', marginBottom: 3 }}>{k}</div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 500, textTransform: 'capitalize' }}>{v}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Compat scores */}
              <div className="wcard" style={{ marginBottom: 16 }}>
                <div className="wcard-pad">
                  <div className="sec-head" style={{ fontSize: '0.95rem', marginBottom: 14 }}><span className="sec-head-icon">✦</span> Compatibility</div>
                  {[
                    { label: 'Wardrobe Match', score: analysis.wardrobe_compatibility.score, detail: `Pairs with ${analysis.wardrobe_compatibility.matching_items_count} items` },
                    { label: 'Body Shape Fit', score: analysis.body_shape_compatibility.score, detail: `For ${analysis.body_shape_compatibility.body_shape} shape` },
                  ].map(({ label, score, detail }) => {
                    const p = (score * 100).toFixed(0);
                    const cls = score >= .8 ? 'green' : score >= .6 ? 'yellow' : 'red';
                    return (
                      <div className="score-bar-wrap" key={label}>
                        <div className="score-bar-top">
                          <span className="score-bar-label">{label}</span>
                          <span className="score-bar-detail">{detail}</span>
                        </div>
                        <div className="score-bar-track">
                          <div className={`score-bar-fill ${cls}`} style={{ width: `${p}%` }} />
                        </div>
                        <div className="score-bar-pct">{p}%</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Matching items */}
              {analysis.wardrobe_compatibility.matching_items.length > 0 && (
                <div className="wcard" style={{ marginBottom: 16 }}>
                  <div className="wcard-pad">
                    <div className="sec-head" style={{ fontSize: '0.95rem', marginBottom: 14 }}><span className="sec-head-icon">✦</span> Pairs Well With</div>
                    {analysis.wardrobe_compatibility.matching_items.map((m, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--white)', borderRadius: 14, padding: '10px 14px', marginBottom: 8 }}>
                        <div style={{ width: 36, height: 36, background: 'var(--pink)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 700, color: 'var(--carnation)', flexShrink: 0 }}>{i + 1}</div>
                        <div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 500, textTransform: 'capitalize' }}>{m.item_color} {m.item_type}</div>
                          <div style={{ fontSize: '0.72rem', color: '#C4A090', textTransform: 'capitalize' }}>{m.harmony_type} harmony</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Duplicate warning */}
              {analysis.duplicate_check.is_duplicate && (
                <div className="alert-w" style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 16 }}>
                  <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: 6 }}>Similar Item in Your Wardrobe</div>
                    {analysis.duplicate_check.similar_items.map((item, i) => (
                      <div key={i} style={{ fontSize: '0.82rem', textTransform: 'capitalize' }}>· {item.item_color} {item.item_type}</div>
                    ))}
                  </div>
                </div>
              )}

              {/* Reasons */}
              <div className="wcard" style={{ marginBottom: 20 }}>
                <div className="wcard-pad">
                  <div className="sec-head" style={{ fontSize: '0.95rem', marginBottom: 14 }}><span className="sec-head-icon">✦</span> Why {analysis.recommendation}?</div>
                  {analysis.reasons.map((r, i) => (
                    <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8, fontSize: '0.83rem', color: 'var(--mid)' }}>
                      <span>{r.includes('✅') || r.includes('🎉') ? '✅' : r.includes('❌') ? '❌' : '💡'}</span>
                      <span style={{ flex: 1 }}>{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="btn-row">
                <button className="btn-s full" onClick={() => { setImage(null); setPreview(''); setAnalysis(null); }}>
                  Analyse Another Item
                </button>
                <button className="btn-p full" onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default Shopping;