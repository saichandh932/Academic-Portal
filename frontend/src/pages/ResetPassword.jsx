import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Lock, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing security token. Please request a new link.");
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const resp = await axios.post("/api/db/password/reset", {
        token: token,
        password: password
      });
      if (resp.data.success) {
        setSuccess(true);
      }
    } catch (err) {
      setError(err.response?.data?.error || "Failed to update password. Link may be expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: '#fafafa', minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '1rem' }}>
      
      <div className="vignan-auth-container animate-fade-in" style={{ padding: '3rem 2rem', width: '100%', maxWidth: '480px' }}>
        
        {success ? (
          <div style={{ textAlign: 'center', width: '100%' }}>
            <CheckCircle size={64} color="var(--success)" style={{ marginBottom: '1.5rem' }} />
            <h2 className="vignan-auth-title">Success <strong>Updated!</strong></h2>
            <p style={{ color: '#666', marginBottom: '2rem' }}>
              Your password has been securely updated. You can now use your new credentials to log in.
            </p>
            <button 
              className="vignan-btn" 
              style={{ width: '100%' }}
              onClick={() => navigate("/")}
            >
              Back to Login
            </button>
          </div>
        ) : (
          <>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
               <img src="/vignan_logo.png" alt="Logo" style={{ height: '70px', marginBottom: '1rem' }} />
               <h2 className="vignan-auth-title" style={{ marginTop: 0 }}>Secure <strong>Reset</strong></h2>
               <p style={{ color: '#666', fontSize: '0.9rem' }}>Choose a new, strong password for your account.</p>
            </div>

            {error && (
              <div style={{ 
                color: 'var(--danger)', 
                background: 'rgba(239, 68, 68, 0.1)', 
                padding: '1rem', 
                borderRadius: '8px', 
                marginBottom: '1.5rem', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.75rem',
                fontSize: '0.85rem'
              }}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="vignan-form-wrapper" style={{ width: '100%' }}>
              
              <div style={{ position: 'relative' }}>
                <input 
                  type={showPassword ? "text" : "password"} 
                  className="vignan-input" 
                  placeholder="New Password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ borderRadius: '8px' }}
                  required
                  disabled={!!error && !token}
                />
                <div 
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', cursor: 'pointer', color: '#999' }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </div>
              </div>

              <input 
                type="password" 
                className="vignan-input" 
                placeholder="Confirm New Password" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={{ borderRadius: '8px' }}
                required
                disabled={!!error && !token}
              />

              <button 
                type="submit" 
                className="vignan-btn" 
                disabled={loading || (!!error && !token)}
                style={{ background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '8px', height: '52px', fontWeight: '800' }}
              >
                {loading ? "Updating..." : "CONFIRM NEW PASSWORD"}
              </button>

              <button 
                type="button" 
                className="vignan-btn" 
                style={{ background: 'transparent', border: '1px solid #ddd', marginTop: '0.5rem' }}
                onClick={() => navigate("/")}
              >
                Cancel
              </button>
            </form>
          </>
        )}

      </div>
    </div>
  );
}
