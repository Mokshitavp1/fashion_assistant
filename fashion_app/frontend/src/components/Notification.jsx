import { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Notification({ id, message, type = 'error', actionLabel, onAction, onClose, autoHide = 6000 }) {
    useEffect(() => {
        if (!autoHide) return;
        const t = setTimeout(() => { onClose && onClose(id); }, autoHide);
        return () => clearTimeout(t);
    }, [id, autoHide, onClose]);

    const colors = {
        error: { bg: 'linear-gradient(90deg,#fef2f2,#fee2e2)', border: '#fca5a5', text: '#991b1b' },
        success: { bg: 'linear-gradient(90deg,#ecfdf5,#d1fae5)', border: '#86efac', text: '#166534' },
        info: { bg: 'linear-gradient(90deg,#fff7ed,#ffedd5)', border: '#fbbf24', text: '#92400e' },
    };
    const c = colors[type] || colors.error;

    return (
        <div style={{
            position: 'fixed', right: 20, bottom: 20, zIndex: 120,
            minWidth: 300, maxWidth: 'calc(100% - 48px)',
        }}>
            <div style={{
                background: c.bg, border: `1.5px solid ${c.border}`, borderRadius: 12, padding: 12,
                boxShadow: '0 8px 28px rgba(0,0,0,0.08)', display: 'flex', gap: 12, alignItems: 'flex-start'
            }}>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, color: c.text, marginBottom: 6 }}>{message}</div>
                    {actionLabel && onAction && (
                        <div style={{ marginTop: 6 }}>
                            <button className="btn-p" onClick={() => onAction(id)} style={{ padding: '8px 12px' }}>{actionLabel}</button>
                        </div>
                    )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    <button onClick={() => onClose && onClose(id)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 6 }} aria-label="close">
                        <X size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
}
