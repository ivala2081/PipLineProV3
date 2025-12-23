import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';
import { ModernHeader } from './ModernHeader';
import { UnifiedNavigation } from '../navigation/UnifiedNavigation';
import { Button } from '../ui/button';
import { Menu } from 'lucide-react';

interface ModernLayoutProps {
  children?: React.ReactNode;
}

const ModernLayout: React.FC<ModernLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { state, setSidebarOpen, setMobileMenuOpen } = useNavigation();

  // #region agent log
  React.useEffect(() => {
    if (!import.meta.env.DEV) return;
    const sidebar = document.querySelector('[class*="sidebar"]') || document.querySelector('.lg\\:fixed');
    if (sidebar) {
      const computed = getComputedStyle(sidebar as HTMLElement);
      fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ModernLayout.tsx:18',message:'Sidebar styles detected',data:{bgColor:computed.backgroundColor,color:computed.color,borderColor:computed.borderColor,width:computed.width},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B'})}).catch(()=>{});
    }
  }, []);
  // #endregion

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Fallback: clear local state and redirect
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Mobile menu overlay */}
      {state.mobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div className="fixed inset-0 bg-black/50" />
        </div>
      )}

      {/* Mobile drawer */}
      <UnifiedNavigation variant="mobile-drawer" />

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <UnifiedNavigation variant="sidebar" />
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <ModernHeader
          onMenuClick={() => setMobileMenuOpen(true)}
          onLogout={handleLogout}
        />

        {/* Page content */}
        <main className="min-h-[calc(100vh-7rem)] bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          {children || <Outlet />}
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <UnifiedNavigation variant="mobile-bottom" />
    </div>
  );
};

export default ModernLayout;
