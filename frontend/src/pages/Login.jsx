import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [role, setRole] = useState('Select User');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Forgot Password States
  const [showForgot, setShowForgot] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [regId, setRegId] = useState('');
  
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (role === 'Select User') {
      setErrorMsg('Please select a valid user type from the dropdown.');
      return;
    }

    if (identifier.trim() === '' || password.trim() === '') {
      setErrorMsg('Please enter both your ID and password.');
      return;
    }

    setLoading(true);

    if (role === 'Staff') {
      try {
        const res = await fetch('/api/dashboard/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: identifier, password: password })
        });
        const data = await res.json();
        
        if (data.success) {
          sessionStorage.setItem('vignan_user_role', 'Staff');
          sessionStorage.setItem('vignan_user_id', identifier);
          navigate(`/admin?subject=${encodeURIComponent(data.assigned_subject)}`);
        } else {
          setErrorMsg(data.error || 'Invalid staff credentials');
        }
      } catch {
        setErrorMsg('Network error. Please try again.');
      }
    } else if (role === 'Student' || role === 'Parent') {
      try {
        const res = await fetch('/api/db/students/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: identifier, password: password })
        });
        const data = await res.json();
        
        if (data.success) {
          sessionStorage.setItem('vignan_user_role', role); // Store as Student or Parent
          sessionStorage.setItem('vignan_user_id', identifier);
          
          if (role === 'Student') {
            navigate(`/student/${identifier}`);
          } else {
            navigate(`/parent/${identifier}`);
          }
        } else {
          setErrorMsg(data.error || `Invalid ${role.toLowerCase()} credentials`);
        }
      } catch {
        setErrorMsg('Network error. Please try again.');
      }
    }
    
    
    setLoading(false);
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    
    if (role === 'Select User' || role === 'Parent') {
      setErrorMsg('Please select a valid user type (Student or Staff).');
      return;
    }

    setLoading(true);
    try {
      const resp = await fetch("/api/db/password/forgot", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ registration_number: regId, role: role })
      });
      const data = await resp.json();
      if (data.success) {
        setResetSent(true);
      } else {
        setErrorMsg(data.error || "Failed to initiate reset.");
      }
    } catch {
      setErrorMsg("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: 'var(--bg-color)', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* 1. Official Header Navbar */}
      <header className="vignan-nav">
        <div>
          {/* Logo pulled directly from your public folder, enlarged for visibility */}
          <img src="/vignan_logo.png" alt="Vignan's Foundation for Science, Technology & Research" className="vignan-logo-img" />
        </div>
      </header>

      {/* 2. Hero Banner */}
      <div className="vignan-hero-banner">
        <img src="/vignan_hero.jpg" alt="Vignan Hero" className="vignan-hero-img" />
        <h1 className="vignan-hero-title">
          VIGNAN <strong>ACADEMIC PORTAL</strong>
        </h1>
      </div>

      {/* 3. Authentication Central Form */}
      <div className="vignan-auth-container animate-fade-in">
        {!showForgot ? (
          <>
            <h2 className="vignan-auth-title">
              SignIn To <strong>Your Account</strong>
            </h2>

            {errorMsg && (
              <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontWeight: '500', background: 'rgba(239, 68, 68, 0.1)', padding: '0.8rem', borderRadius: '4px', width: '100%', maxWidth: '480px', textAlign: 'center' }}>
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleLogin} className="vignan-form-wrapper">
              
              <input 
                type="text" 
                className="vignan-input" 
                placeholder="Registerno or Empcode" 
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />

              <select 
                className={`vignan-input vignan-select ${role !== 'Select User' ? 'vignan-select-active' : ''}`}
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="Select User">Select User</option>
                <option value="Student">Student</option>
                <option value="Parent">Parent</option>
                <option value="Staff">Staff</option>
              </select>

              <input 
                type="password" 
                className="vignan-input" 
                placeholder="Password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <button type="submit" className="vignan-btn" disabled={loading}>
                {loading ? "Authenticating..." : "Login"}
              </button>

            </form>

            <a href="#" className="vignan-forgot-link" onClick={(e) => { e.preventDefault(); setShowForgot(true); setErrorMsg(''); setRegId(identifier); }}>
              Forgot or Set password?
            </a>
          </>
        ) : (
          <div className="animate-fade-in" style={{ width: '100%', maxWidth: '480px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
             {resetSent ? (
               <div style={{ textAlign: 'center', width: '100%' }}>
                  <h2 className="vignan-auth-title">Link <strong>Dispatched!</strong></h2>
                  <p style={{ color: '#666', marginBottom: '2rem' }}>
                    A secure reset link has been sent to your university email. Please check your inbox (and spam folder) to proceed.
                  </p>
                  <button 
                    className="vignan-btn" 
                    onClick={() => { setShowForgot(false); setResetSent(false); }}
                  >
                    Return to Login
                  </button>
               </div>
             ) : (
               <>
                  <h2 className="vignan-auth-title">Reset <strong>Password</strong></h2>
                  <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1.5rem', textAlign: 'center' }}>
                    Select your role and enter your ID to receive a secure link.
                  </p>
                  
                  {errorMsg && (
                    <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontWeight: '500', background: 'rgba(239, 68, 68, 0.1)', padding: '0.8rem', borderRadius: '4px', width: '100%', textAlign: 'center' }}>
                      {errorMsg}
                    </div>
                  )}

                  <form onSubmit={handleForgotSubmit} className="vignan-form-wrapper" style={{ width: '100%' }}>
                    <select 
                      className={`vignan-input vignan-select ${role !== 'Select User' ? 'vignan-select-active' : ''}`}
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                    >
                      <option value="Select User">Select User</option>
                      <option value="Student">Student</option>
                      <option value="Staff">Staff</option>
                    </select>

                    <input 
                      type="text" 
                      className="vignan-input" 
                      placeholder="University ID / Reg Number" 
                      value={regId}
                      onChange={(e) => setRegId(e.target.value)}
                      required
                    />

                    <button type="submit" className="vignan-btn" disabled={loading} style={{ background: 'var(--primary)', color: 'white', border: 'none' }}>
                      {loading ? "Processing..." : "Send Reset Link"}
                    </button>
                    
                    <button 
                      type="button" 
                      className="vignan-btn" 
                      style={{ background: 'transparent', border: '1px solid #ddd', marginTop: '0.5rem' }}
                      onClick={() => setShowForgot(false)}
                    >
                      Back
                    </button>
                  </form>
               </>
             )}
          </div>
        )}
      </div>

    </div>
  );
}
