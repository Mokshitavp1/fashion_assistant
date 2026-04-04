import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOutfitRecommendations, rateOutfit } from '../services/api';
import { ArrowLeft, Sparkles, TrendingUp, Palette, User, Star } from 'lucide-react';
import { sharedCSS } from './sharedStyles';

function Outfits() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [outfits, setOutfits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOutfits = useCallback(async () => {
    try {
      const r = await getOutfitRecommendations(userId, 10);
      setOutfits(r.data.recommended_outfits);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate outfits');
    } finally { setLoading(false); }
  }, [userId]);

  useEffect(() => {
    if (!userId) { navigate('/onboarding'); return; }
    fetchOutfits();
  }, [fetchOutfits, userId, navigate]);

  if (loading) return (
    <><style>{sharedCSS}</style>
      <div className="loader-wrap"><div className="loader-ring" />
        <p className="loader-text">Curating your perfect looks…</p>
      </div>
    </>
  );

  const emptyMsg = error
    ? { title: 'Unable to Generate Outfits', body: error, action: 'Go to Wardrobe', path: '/wardrobe' }
    : { title: 'Not Enough Items', body: 'Add at least 2 items to your wardrobe to get outfit recommendations.', action: 'Add Items', path: '/wardrobe' };

  return (
    <>
      <style>{sharedCSS}</style>
      <div className="pg">
        <nav className="pg-nav">
          <div className="pg-nav-left">
            <button className="pg-back" onClick={() => navigate('/dashboard')}><ArrowLeft size={13} /> Dashboard</button>
            <span className="pg-title"><Sparkles size={15} className="pg-title-icon" /> Outfit Recommendations</span>
          </div>
        </nav>

        <div className="pg-body-narrow">
          {(error || outfits.length === 0) ? (
            <div className="wcard">
              <div style={{ textAlign: 'center', padding: '60px 24px' }}>
                <div style={{ width: 64, height: 64, background: 'var(--pink)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px' }}>
                  <Sparkles size={28} style={{ color: 'var(--carnation)' }} />
                </div>
                <div style={{ fontFamily: 'Playfair Display,serif', fontSize: '1.35rem', fontStyle: 'italic', marginBottom: 8 }}>{emptyMsg.title}</div>
                <p style={{ color: 'var(--mid)', marginBottom: 22, fontSize: '0.88rem' }}>{emptyMsg.body}</p>
                <button className="btn-p" onClick={() => navigate(emptyMsg.path)}>{emptyMsg.action}</button>
              </div>
            </div>
          ) : (
            outfits.map(outfit => <OutfitCard key={outfit.outfit_number} outfit={outfit} />)
          )}
        </div>
      </div>
    </>
  );
}

const scoreColor = s => s >= .8 ? 'green' : s >= .6 ? 'yellow' : 'red';
const scoreLabel = s => s >= .8 ? 'Excellent' : s >= .6 ? 'Good' : 'Fair';
const catEmoji = c => ({ top: '👕', bottom: '👖', dress: '👗', shoes: '👟', accessories: '👜' }[c?.toLowerCase()] || '👔');

function OutfitCard({ outfit }) {
  const pct = (s) => (s * 100).toFixed(0);
  const userId = localStorage.getItem('userId');
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isRating, setIsRating] = useState(false);
  const [ratingSubmitted, setRatingSubmitted] = useState(false);

  const handleSubmitRating = async () => {
    if (rating === 0) return;
    setIsRating(true);
    try {
      await rateOutfit(userId, outfit.outfit_number, rating, comment || null);
      setRatingSubmitted(true);
      setTimeout(() => setRatingSubmitted(false), 3000);
      setRating(0);
      setComment('');
    } catch (e) {
      console.error('Failed to submit rating:', e);
    } finally {
      setIsRating(false);
    }
  };

  return (
    <div className="outfit-card">
      <div className="outfit-card-head">
        <div>
          <div className="outfit-card-num">Outfit #{outfit.outfit_number}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--mid)', marginTop: 3, fontFamily: 'Cormorant Garamond,serif', fontStyle: 'italic' }}>
            {scoreLabel(outfit.overall_score)} Match
          </div>
        </div>
        <div className="outfit-card-score-badge">{pct(outfit.overall_score)}%</div>
      </div>

      <div className="outfit-card-body">
        {/* Score breakdown */}
        <div className="outfit-scores">
          {[
            { icon: <Palette size={15} />, label: 'Color Harmony', score: outfit.color_harmony_score },
            { icon: <User size={15} />, label: 'Body Shape', score: outfit.body_shape_score },
            { icon: <TrendingUp size={15} />, label: 'Undertone', score: outfit.undertone_score },
          ].map(({ icon, label, score }) => (
            <div className="outfit-score-item" key={label}>
              <div className="outfit-score-icon">{icon}</div>
              <div className="outfit-score-label">{label}</div>
              <div className="score-bar-track" style={{ maxWidth: 80, margin: '0 auto 4px' }}>
                <div className={`score-bar-fill ${scoreColor(score)}`} style={{ width: `${pct(score)}%` }} />
              </div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--dark)' }}>{pct(score)}%</div>
            </div>
          ))}
        </div>

        {/* Items list */}
        <div className="sec-head" style={{ marginBottom: 12, fontSize: '0.88rem' }}>
          <span className="sec-head-icon">✦</span> Items in this outfit
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {outfit.items.map(item => (
            <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--white)', borderRadius: 14, padding: '10px 14px' }}>
              <div style={{ width: 40, height: 40, background: 'var(--pink)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', flexShrink: 0 }}>
                {catEmoji(item.category)}
              </div>
              <div>
                <div style={{ fontSize: '0.88rem', fontWeight: 500, color: 'var(--dark)', textTransform: 'capitalize' }}>{item.color} {item.type}</div>
                <div style={{ fontSize: '0.72rem', color: '#C4A090', textTransform: 'capitalize' }}>{item.pattern} · {item.category}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Rating section */}
        <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--light)' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 500, marginBottom: 8, color: 'var(--dark)' }}>
            How well does this outfit work for you?
          </div>
          <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
            {[1, 2, 3, 4, 5].map(star => (
              <button
                key={star}
                onClick={() => setRating(star)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 4,
                  fontSize: '1.4rem',
                  opacity: star <= rating ? 1 : 0.3,
                  transition: 'opacity 0.2s',
                }}
              >
                <Star size={20} fill={star <= rating ? 'var(--carnation)' : 'none'} color="var(--carnation)" />
              </button>
            ))}
          </div>
          {rating > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <textarea
                placeholder="Optional: What do you like or dislike about this outfit?"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                style={{
                  borderRadius: 8,
                  border: '1px solid var(--pink)',
                  padding: '8px 12px',
                  fontSize: '0.8rem',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                  minHeight: 50,
                }}
              />
              <button
                onClick={handleSubmitRating}
                disabled={isRating}
                style={{
                  background: 'var(--carnation)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  padding: '8px 12px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  opacity: isRating ? 0.6 : 1,
                }}
              >
                {isRating ? 'Submitting...' : 'Submit Rating'}
              </button>
              {ratingSubmitted && (
                <div style={{ color: 'var(--carnation)', fontSize: '0.8rem', fontWeight: 500 }}>
                  ✓ Thanks for your feedback! This helps improve our recommendations.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Outfits;