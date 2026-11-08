import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sprout, ArrowLeft, Eye, EyeOff, Mail, Lock, User, Globe2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const AuthPage: React.FC = () => {
 const { login, register } = useAuth();
 const location=useLocation(); const navigate=useNavigate();
 const requestedMode=new URLSearchParams(location.search).get('mode');
 const initialMode=(requestedMode==='signup'||location.pathname==='/signup')?'signup':'signin';
 const [mode,setMode]=useState<'signin'|'signup'>(initialMode);
 const [showPassword,setShowPassword]=useState(false); const [name,setName]=useState(''); const [email,setEmail]=useState(''); const [password,setPassword]=useState('');
 const [busy,setBusy]=useState(false); const [message,setMessage]=useState('');
 const submit=async(e:React.FormEvent)=>{
   e.preventDefault();
   setBusy(true);
   setMessage('');
   try{
     if (mode === 'signup') {
       await register(name, email, password);
       setMessage('Account created successfully! Opening your dashboard…');
     } else {
       await login(email, password);
       setMessage('Welcome back! Opening your dashboard…');
     }
   }catch(err: any){
     const msg = err?.response?.data?.detail || err?.response?.data?.error?.message || err?.message || 'Could not authenticate.';
     setMessage(msg);
   }finally{
     setBusy(false);
   }
 };
 return <main className="auth-shell">
  <div className="auth-top"><Link to="/" className="agri-brand"><span className="brand-mark"><Sprout size={25}/></span><span><b>AgriPulse</b><small>Smart Farming · Sustainable Future</small></span></Link><Link to="/" className="back-home"><ArrowLeft size={16}/> Back to home</Link></div>
  <div className={'auth-card '+(mode==='signup'?'signup-mode':'signin-mode')}>
   <div className="auth-visual"><div className="auth-visual-shade"/><div className="visual-label"><span className="visual-logo"><Sprout size={25}/></span><span>AGRI PULSE <small>FARM SMARTER</small></span></div><div className="visual-copy"><span className="eyebrow">GROW A BETTER TOMORROW</span><h1>{mode==='signin'?'Welcome back to your fields.':'Your next chapter starts here.'}</h1><p>Insights for healthier crops, smarter water use, and a more sustainable future.</p></div><div className="visual-bottom"><span><Globe2 size={17}/> Made for farmers everywhere</span><span>01 / 02</span></div></div>
   <div className="auth-form-panel"><div className="auth-switch"><button className={mode==='signin'?'active':''} onClick={()=>{setMode('signin');setMessage('');navigate('/signin',{replace:true})}}>Sign in</button><button className={mode==='signup'?'active':''} onClick={()=>{setMode('signup');setMessage('');navigate('/signup',{replace:true})}}>Create account</button></div>
    <div className="auth-form-heading"><span className="eyebrow dark">{mode==='signin'?'GOOD TO SEE YOU':'JOIN AGRIPULSE'}</span><h2>{mode==='signin'?'Sign in':'Create your account'}</h2><p>{mode==='signin'?'Enter your details to continue to your dashboard.':'Start making more informed farming decisions.'}</p></div>
    <form onSubmit={submit} className="auth-form">{mode==='signup'&&<label><span>Full name</span><div className="auth-input"><User size={18}/><input autoComplete="name" required value={name} onChange={e=>setName(e.target.value)} placeholder="Your name" className="placeholder:text-slate-600 w-full border-none bg-transparent outline-none"/></div></label>}
      <label><span>Email address</span><div className="auth-input"><Mail size={18}/><input type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com"/></div></label>
      <label><span>Password</span><div className="auth-input"><Lock size={18}/><input type={showPassword?'text':'password'} autoComplete={mode==='signin'?'current-password':'new-password'} minLength={8} required value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters"/><button type="button" className="show-password" onClick={()=>setShowPassword(!showPassword)} aria-label="Toggle password visibility">{showPassword?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></label>
      <button className="auth-submit" disabled={busy}>{busy?'Please wait…':mode==='signin'?'Sign in to AgriPulse':'Create account'} <span>→</span></button>
    </form>
    {message&&<p className={message.toLowerCase().includes('needs')||message.toLowerCase().includes('could not')?'auth-message error':'auth-message'} role="status">{message}</p>}
    <p className="auth-terms">By continuing, you agree to our <a href="#terms">Terms</a> and <a href="#privacy">Privacy Policy</a>.</p>
    <p className="auth-switch-hint">{mode==='signin'?<>New to AgriPulse? <button type="button" onClick={()=>{setMode('signup');setMessage('');navigate('/signup',{replace:true})}}>Create an account</button></>:<>Already have an account? <button type="button" onClick={()=>{setMode('signin');setMessage('');navigate('/signin',{replace:true})}}>Sign in</button></>}</p>
   </div>
  </div>
  <footer className="auth-footer">© 2026 AgriPulse <span>·</span> Sustainable farming, shared worldwide.</footer>
 </main>;
};
