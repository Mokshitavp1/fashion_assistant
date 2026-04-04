import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWardrobe, addWardrobeItem, deleteWardrobeItem } from '../services/api';
import { ArrowLeft, Plus, Trash2, Upload, AlertTriangle } from 'lucide-react';
import { sharedCSS } from './sharedStyles';

const IMAGE_BASE_URL = 'http://127.0.0.1:8000';

function Wardrobe() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const fetchWardrobe = useCallback(async () => {
    try {
      const r = await getWardrobe(userId);
      setItems(r.data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (!userId) { navigate('/onboarding'); return; }
    fetchWardrobe();
  }, [fetchWardrobe, userId, navigate]);

  const handleDelete = async (id) => {
    if (!confirm('Remove this item from your wardrobe?')) return;
    try {
      await deleteWardrobeItem(userId, id);
      setItems(items.filter(i => i.id !== id));
    } catch (e) { alert('Failed to delete item'); }
  };

  if (loading) {
    return (
      <>
        <style>{sharedCSS}</style>
        <div className="loader-wrap">
          <div className="loader-ring" />
          <p className="loader-text">Loading your wardrobe…</p>
        </div>
      </>
    );
  }

  return (
    <>
      <style>{sharedCSS}{`
        .ward-empty {
          text-align:center; padding:80px 24px;
        }
        .ward-empty-icon {
          width:80px; height:80px;
          background:var(--pink); border-radius:50%;
          display:flex; align-items:center; justify-content:center;
          color:var(--carnation); margin:0 auto 20px;
        }
        .ward-empty-title {
          font-family:'Playfair Display',serif;
          font-size:1.5rem; font-style:italic; color:var(--dark); margin-bottom:8px;
        }
        .ward-empty-sub { font-size:0.85rem; color:var(--mid); margin-bottom:24px; }
      `}</style>

      <div className="pg">
        <nav className="pg-nav">
          <div className="pg-nav-left">
            <button className="pg-back" onClick={() => navigate('/dashboard')}>
              <ArrowLeft size={13} /> Dashboard
            </button>
            <span className="pg-title">
              <span className="pg-title-icon">✦</span> My Wardrobe
            </span>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn-warn" onClick={() => navigate('/discard')}>
              <AlertTriangle size={14} /> Discard Analysis
            </button>
            <button className="btn-p" onClick={() => setShowModal(true)}>
              <Plus size={14} /> Add Item
            </button>
          </div>
        </nav>

        <div className="pg-body">
          {items.length === 0 ? (
            <div className="wcard">
              <div className="ward-empty">
                <div className="ward-empty-icon"><Upload size={32} /></div>
                <div className="ward-empty-title">Your wardrobe is empty</div>
                <div className="ward-empty-sub">Add clothing items to get personalised recommendations</div>
                <button className="btn-p" onClick={() => setShowModal(true)}>
                  <Plus size={14} /> Add Your First Item
                </button>
              </div>
            </div>
          ) : (
            <div className="g4">
              {items.map(item => (
                <ClothCard key={item.id} item={item} onDelete={() => handleDelete(item.id)} />
              ))}
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <AddModal
          userId={userId}
          onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); fetchWardrobe(); }}
        />
      )}
    </>
  );
}

function ClothCard({ item, onDelete }) {
  const [err, setErr] = useState(false);

  const getUrl = () => {
    const token = localStorage.getItem('accessToken');
    const withToken = (url) => {
      if (!url || !token || !url.includes('/images/')) return url;
      return `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`;
    };
    if (item.image_url) {
      const abs = item.image_url.startsWith('http') ? item.image_url : `${IMAGE_BASE_URL}${item.image_url.startsWith('/') ? '' : '/'}${item.image_url}`;
      return withToken(abs);
    }
    if (!item.image_path) return null;
    const fn = String(item.image_path).replace(/\\/g, '/').split('/').pop();
    return `${IMAGE_BASE_URL}/uploads/${fn}`;
  };

  const url = getUrl();

  return (
    <div className="cloth-card">
      <div className="cloth-card-img">
        {url && !err
          ? <img src={url} alt={`${item.color_primary} ${item.type}`} onError={() => setErr(true)} />
          : <span className="placeholder">👗</span>
        }
        <button className="cloth-del-btn" onClick={onDelete}><Trash2 size={13} /></button>
      </div>
      <div className="cloth-card-body">
        <div className="cloth-card-pills">
          <span className="pill pill-peach">{item.category}</span>
          <span className="pill pill-gray">{item.season}</span>
        </div>
      </div>
    </div>
  );
}

function AddModal({ userId, onClose, onSuccess }) {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [category, setCategory] = useState('top');
  const [season, setSeason] = useState('all');
  const [loading, setLoading] = useState(false);

  const handleImg = (e) => {
    const f = e.target.files[0];
    if (f) { setImage(f); setPreview(URL.createObjectURL(f)); }
  };

  const handleSubmit = async () => {
    if (!image) { alert('Please select an image'); return; }
    setLoading(true);
    try {
      await addWardrobeItem(userId, image, category, season);
      onSuccess();
    } catch (e) { alert('Failed to add item'); }
    finally { setLoading(false); }
  };

  return (
    <div className="modal-bg">
      <div className="modal-box">
        <div className="modal-head">
          <div className="modal-head-title">Add Clothing Item</div>
        </div>
        <div className="modal-body">
          <div className="ff">
            <label>Photo</label>
            <div className="upload-zone">
              <input type="file" accept="image/*" onChange={handleImg} style={{ display: 'none' }} id="item-up" />
              <label htmlFor="item-up" style={{ cursor: 'pointer', display: 'block' }}>
                {preview
                  ? <img src={preview} alt="preview" style={{ maxHeight: 180, borderRadius: 12, margin: '0 auto', display: 'block' }} />
                  : <div>
                    <Upload size={32} style={{ margin: '0 auto 10px', display: 'block', color: 'var(--pink)' }} />
                    <div style={{ fontSize: '0.88rem', color: 'var(--mid)' }}>Click to upload</div>
                    <div style={{ fontSize: '0.72rem', color: '#C4A090', marginTop: 3 }}>PNG, JPG up to 10MB</div>
                  </div>
                }
              </label>
            </div>
          </div>
          <div className="g2">
            <div className="ff">
              <label>Category</label>
              <select value={category} onChange={e => setCategory(e.target.value)}>
                <option value="top">Top</option>
                <option value="bottom">Bottom</option>
                <option value="dress">Dress</option>
                <option value="shoes">Shoes</option>
                <option value="accessories">Accessories</option>
              </select>
            </div>
            <div className="ff">
              <label>Season</label>
              <select value={season} onChange={e => setSeason(e.target.value)}>
                <option value="all">All Seasons</option>
                <option value="summer">Summer</option>
                <option value="winter">Winter</option>
                <option value="spring">Spring</option>
                <option value="fall">Fall</option>
              </select>
            </div>
          </div>
          <div className="btn-row" style={{ marginTop: 20 }}>
            <button className="btn-s full" onClick={onClose} disabled={loading}>Cancel</button>
            <button className="btn-p full" onClick={handleSubmit} disabled={loading}>
              {loading ? 'Adding…' : 'Add Item'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Wardrobe;