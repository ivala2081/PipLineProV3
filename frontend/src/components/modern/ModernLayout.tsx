import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';
import { ModernHeader } from './ModernHeader';
import { UnifiedNavigation } from '../navigation/UnifiedNavigation';
import { BreadcrumbNavigation } from '../navigation/BreadcrumbNavigation';
import { Button } from '../ui/button';
import { Menu } from 'lucide-react';

interface ModernLayoutProps {
  children?: React.ReactNode;
}

const ModernLayout: React.FC<ModernLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { state, setSidebarOpen, setMobileMenuOpen } = useNavigation();

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
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }} className="min-h-screen bg-gray-50">
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

        {/* Breadcrumb Navigation */}
        <div className="px-6 py-3 bg-white border-b border-gray-200">
          <BreadcrumbNavigation />
        </div>

        {/* Page content */}
        <main className="min-h-[calc(100vh-7rem)] bg-gray-50">
          {children || <Outlet />}
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <UnifiedNavigation variant="mobile-bottom" />
    </div>
  );
};

export default ModernLayout;
