import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function SignUp() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await signup(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Failed to create account');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'sans-serif' }}>
      <h2>Create Your Peblo TV Account</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '300px' }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: '0.5rem' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ padding: '0.5rem' }}
        />
        <button type="submit" style={{ padding: '0.5rem', cursor: 'pointer', backgroundColor: '#ffcc00', border: 'none', fontWeight: 'bold' }}>
          Create Account
        </button>
        {error && <p style={{ color: 'red', fontSize: '0.8rem' }}>{error}</p>}
        <p style={{ textAlign: 'center', fontSize: '0.9rem' }}>
          Already have an account? <Link to="/login">Log In</Link>
        </p>
      </form>
    </div>
  );
}
