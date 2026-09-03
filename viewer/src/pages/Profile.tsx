import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { updateProfile, updateEmail } from 'firebase/auth';
import { auth } from '../firebase';

export default function Profile() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [displayName, setDisplayName] = useState(user?.displayName || '');
  const [email, setEmail] = useState(user?.email || '');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (user) {
      setDisplayName(user.displayName || '');
      setEmail(user.email || '');
    }
  }, [user]);

  const handleSave = async () => {
    if (!user || !auth) {
      setMessage({ type: 'error', text: 'User not authenticated' });
      return;
    }

    setIsSaving(true);
    try {
      const updates: any = {};
      if (displayName !== (user.displayName || '')) {
        updates.displayName = displayName;
      }

      if (displayName !== (user.displayName || '')) {
        await updateProfile(user, { displayName });
      }

      if (email !== user.email) {
        await updateEmail(user, email);
      }

      setIsEditing(false);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update profile' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '600px', margin: '2rem auto' }}>
      <h1 style={{ marginBottom: '2rem' }}>My Profile</h1>

      {message && (
        <div style={{
          backgroundColor: message.type === 'success' ? '#4caf50' : '#ff6b6b',
          color: 'white',
          padding: '1rem',
          borderRadius: '4px',
          marginBottom: '1.5rem',
          fontSize: '0.95rem',
        }}>
          {message.text}
        </div>
      )}

      {/* Profile Card */}
      <div style={{ 
        backgroundColor: 'var(--card-bg)', 
        padding: '2rem', 
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
            Display Name
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            disabled={!isEditing}
            placeholder="Your name"
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem',
              border: isEditing ? `2px solid #ffcc00` : `1px solid #ddd`,
              borderRadius: '4px',
              backgroundColor: isEditing ? 'var(--bg-secondary)' : '#f9f9f9',
              color: 'var(--ink)',
              cursor: isEditing ? 'text' : 'not-allowed',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={!isEditing}
            placeholder="your@email.com"
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem',
              border: isEditing ? `2px solid #ffcc00` : `1px solid #ddd`,
              borderRadius: '4px',
              backgroundColor: isEditing ? 'var(--bg-secondary)' : '#f9f9f9',
              color: 'var(--ink)',
              cursor: isEditing ? 'text' : 'not-allowed',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
            User ID
          </label>
          <p style={{ 
            fontSize: '0.9rem', 
            fontFamily: 'monospace', 
            color: '#999',
            padding: '0.75rem',
            backgroundColor: '#f9f9f9',
            borderRadius: '4px',
            wordBreak: 'break-all',
          }}>
            {user?.uid || 'N/A'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                backgroundColor: '#ffcc00',
                color: '#000',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '1rem',
              }}
            >
              ✏️ Edit Profile
            </button>
          ) : (
            <>
              <button
                onClick={handleSave}
                disabled={isSaving}
                style={{
                  flex: 1,
                  padding: '0.75rem 1rem',
                  backgroundColor: '#4caf50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: isSaving ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  opacity: isSaving ? 0.6 : 1,
                }}
              >
                {isSaving ? '💾 Saving...' : '💾 Save Changes'}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setDisplayName(user?.displayName || '');
                  setEmail(user?.email || '');
                }}
                style={{
                  flex: 1,
                  padding: '0.75rem 1rem',
                  backgroundColor: '#999',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                }}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
