import React, { StrictMode } from 'react';
import { BrowserRouter } from 'react-router-dom';





import { createRoot } from 'react-dom/client'
import './index.css';
import './styles/form.css'
import './styles/dashboardLinks.css'
import App from './App.tsx'
import { AuthProvider } from './context/AuthContext';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
