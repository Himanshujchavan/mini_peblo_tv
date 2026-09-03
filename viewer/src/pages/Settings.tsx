import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '600px', margin: '2rem auto' }}>
      <h1 style={{ marginBottom: '2rem' }}>Settings</h1>

      {/* Theme Section */}
      <div style={{ 
        backgroundColor: 'var(--card-bg)', 
        padding: '2rem', 
        borderRadius: '8px', 
        marginBottom: '2rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '1rem' }}>🎨 Appearance</h2>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '0.25rem' }}>
              Dark Mode
            </p>
            <p style={{ color: '#666', fontSize: '0.9rem' }}>
              Current: <strong>{theme === 'dark' ? '🌙 Dark' : '☀️ Light'}</strong>
            </p>
          </div>
          <button
            onClick={toggleTheme}
            style={{
              padding: '0.5rem 1.5rem',
              backgroundColor: theme === 'dark' ? '#333' : '#ffcc00',
              color: theme === 'dark' ? '#fff' : '#000',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.9rem',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
            }}
          >
            Toggle
          </button>
        </div>
      </div>

      {/* Logout Section */}
      <div style={{ 
        backgroundColor: 'var(--card-bg)', 
        padding: '2rem', 
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '1rem' }}>🔐 Account</h2>
        <button
          onClick={handleLogout}
          style={{
            width: '100%',
            padding: '0.75rem 1rem',
            backgroundColor: '#ff6b6b',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '1rem',
            transition: 'background-color 0.2s',
          }}
          onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#ff5252')}
          onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#ff6b6b')}
        >
          🚪 Log Out
        </button>
      </div>
    </div>
  );
}
