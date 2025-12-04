import React, { useState } from 'react';
import { 
  BarChart3, 
  LineChart, 
  TrendingUp, 
  Shield, 
  DollarSign, 
  Users, 
  Settings,
  FileText,
  Database,
  Activity
} from 'lucide-react';
import {
  CardTabs,
  CardTabItem,
  UnderlineTabs,
  UnderlineTabItem,
  SegmentedTabs,
  SegmentedTabItem,
  PillTabs,
  PillTabItem,
  MinimalTabs,
  MinimalTabItem,
  TabContent
} from './ui/professional-tabs';
import {
  CleanTabs,
  CleanTabItem,
  SubtleTabs,
  SubtleTabItem,
  ElegantTabs,
  ElegantTabItem,
  ModernTabs,
  ModernTabItem,
  MinimalTabContent
} from './ui/minimal-tabs';

const TabShowcase: React.FC = () => {
  const [activeCardTab, setActiveCardTab] = useState('overview');
  const [activeUnderlineTab, setActiveUnderlineTab] = useState('analytics');
  const [activeSegmentedTab, setActiveSegmentedTab] = useState('daily');
  const [activePillTab, setActivePillTab] = useState('revenue');
  const [activeMinimalTab, setActiveMinimalTab] = useState('dashboard');
  const [activeCleanTab, setActiveCleanTab] = useState('overview');
  const [activeSubtleTab, setActiveSubtleTab] = useState('analytics');
  const [activeElegantTab, setActiveElegantTab] = useState('reports');
  const [activeModernTab, setActiveModernTab] = useState('settings');

  const cardTabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3, badge: '12' },
    { id: 'analytics', label: 'Analytics', icon: LineChart, badge: '5' },
    { id: 'performance', label: 'Performance', icon: TrendingUp },
    { id: 'monitoring', label: 'Monitoring', icon: Shield, badge: '!' },
    { id: 'financial', label: 'Financial', icon: DollarSign }
  ];

  const underlineTabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'analytics', label: 'Analytics', icon: LineChart },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  const segmentedTabs = [
    { id: 'daily', label: 'Daily' },
    { id: 'weekly', label: 'Weekly' },
    { id: 'monthly', label: 'Monthly' },
    { id: 'yearly', label: 'Yearly' }
  ];

  const pillTabs = [
    { id: 'revenue', label: 'Revenue', icon: DollarSign },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'transactions', label: 'Transactions', icon: Activity },
    { id: 'database', label: 'Database', icon: Database }
  ];

  const minimalTabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'reports', label: 'Reports' },
    { id: 'settings', label: 'Settings' }
  ];

  return (
    <div className="space-y-12 p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Professional Tab Designs</h1>
        <p className="text-gray-600 mb-8">Comprehensive showcase of business-oriented tab components for PipLinePro</p>

        {/* Card Tabs - Primary Navigation */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Card Tabs - Primary Navigation</h2>
          <p className="text-gray-600 mb-4">Perfect for main dashboard navigation with icons and badges</p>
          
          <CardTabs className="mb-6">
            {cardTabs.map((tab) => (
              <CardTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                icon={tab.icon}
                badge={tab.badge}
                active={activeCardTab === tab.id}
                onClick={() => setActiveCardTab(tab.id)}
              />
            ))}
          </CardTabs>

          <TabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {cardTabs.find(tab => tab.id === activeCardTab)?.label} Content
              </h3>
              <p className="text-gray-600">
                This is the content for the {activeCardTab} tab. Card tabs are ideal for primary navigation 
                with their elevated appearance and support for icons and badges.
              </p>
            </div>
          </TabContent>
        </section>

        {/* Underline Tabs - Secondary Navigation */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Underline Tabs - Secondary Navigation</h2>
          <p className="text-gray-600 mb-4">Clean, minimal design perfect for secondary navigation</p>
          
          <UnderlineTabs className="mb-6">
            {underlineTabs.map((tab) => (
              <UnderlineTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                icon={tab.icon}
                active={activeUnderlineTab === tab.id}
                onClick={() => setActiveUnderlineTab(tab.id)}
              />
            ))}
          </UnderlineTabs>

          <TabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {underlineTabs.find(tab => tab.id === activeUnderlineTab)?.label} Content
              </h3>
              <p className="text-gray-600">
                Underline tabs provide a clean, professional look that doesn't distract from content. 
                Perfect for secondary navigation within sections.
              </p>
            </div>
          </TabContent>
        </section>

        {/* Segmented Tabs - Data Controls */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Segmented Tabs - Data Controls</h2>
          <p className="text-gray-600 mb-4">Ideal for data filtering and time period selection</p>
          
          <SegmentedTabs className="mb-6">
            {segmentedTabs.map((tab) => (
              <SegmentedTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                active={activeSegmentedTab === tab.id}
                onClick={() => setActiveSegmentedTab(tab.id)}
              />
            ))}
          </SegmentedTabs>

          <TabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {segmentedTabs.find(tab => tab.id === activeSegmentedTab)?.label} View
              </h3>
              <p className="text-gray-600">
                Segmented controls are perfect for switching between different data views or time periods. 
                They provide clear visual feedback and are easy to use.
              </p>
            </div>
          </TabContent>
        </section>

        {/* Pill Tabs - Compact Navigation */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Pill Tabs - Compact Navigation</h2>
          <p className="text-gray-600 mb-4">Space-efficient design for compact interfaces</p>
          
          <PillTabs className="mb-6">
            {pillTabs.map((tab) => (
              <PillTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                icon={tab.icon}
                active={activePillTab === tab.id}
                onClick={() => setActivePillTab(tab.id)}
              />
            ))}
          </PillTabs>

          <TabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {pillTabs.find(tab => tab.id === activePillTab)?.label} Section
              </h3>
              <p className="text-gray-600">
                Pill tabs are great for compact interfaces where space is at a premium. 
                They maintain functionality while taking up minimal space.
              </p>
            </div>
          </TabContent>
        </section>

        {/* Minimal Tabs - Clean Text Navigation */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Minimal Tabs - Clean Text Navigation</h2>
          <p className="text-gray-600 mb-4">Ultra-clean design that focuses on content</p>
          
          <MinimalTabs className="mb-6">
            {minimalTabs.map((tab) => (
              <MinimalTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                active={activeMinimalTab === tab.id}
                onClick={() => setActiveMinimalTab(tab.id)}
              />
            ))}
          </MinimalTabs>

          <TabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {minimalTabs.find(tab => tab.id === activeMinimalTab)?.label} Page
              </h3>
              <p className="text-gray-600">
                Minimal tabs provide the cleanest possible interface, perfect for content-focused applications 
                where navigation should be unobtrusive.
              </p>
            </div>
          </TabContent>
        </section>

        {/* Clean Tabs - No Borders, Just Hover Effects */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Clean Tabs - No Borders</h2>
          <p className="text-gray-600 mb-4">Completely borderless with subtle hover effects</p>
          
          <CleanTabs className="mb-6">
            {cardTabs.map((tab) => (
              <CleanTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                icon={tab.icon}
                badge={tab.badge}
                active={activeCleanTab === tab.id}
                onClick={() => setActiveCleanTab(tab.id)}
              />
            ))}
          </CleanTabs>

          <MinimalTabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {cardTabs.find(tab => tab.id === activeCleanTab)?.label} Content
              </h3>
              <p className="text-gray-600">
                Clean tabs remove all visual clutter, focusing purely on typography and subtle hover effects. 
                Perfect for minimalist interfaces.
              </p>
            </div>
          </MinimalTabContent>
        </section>

        {/* Subtle Tabs - Light Background Hover */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Subtle Tabs - Light Background</h2>
          <p className="text-gray-600 mb-4">Very light background appears on hover</p>
          
          <SubtleTabs className="mb-6">
            {underlineTabs.map((tab) => (
              <SubtleTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                icon={tab.icon}
                active={activeSubtleTab === tab.id}
                onClick={() => setActiveSubtleTab(tab.id)}
              />
            ))}
          </SubtleTabs>

          <MinimalTabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {underlineTabs.find(tab => tab.id === activeSubtleTab)?.label} Section
              </h3>
              <p className="text-gray-600">
                Subtle tabs provide gentle visual feedback with light background colors on hover. 
                Great for interfaces that need minimal visual noise.
              </p>
            </div>
          </MinimalTabContent>
        </section>

        {/* Elegant Tabs - Animated Underline */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Elegant Tabs - Animated Underline</h2>
          <p className="text-gray-600 mb-4">Smooth animated underline effect on hover and active</p>
          
          <ElegantTabs className="mb-6">
            {segmentedTabs.map((tab) => (
              <ElegantTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                active={activeElegantTab === tab.id}
                onClick={() => setActiveElegantTab(tab.id)}
              />
            ))}
          </ElegantTabs>

          <MinimalTabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {segmentedTabs.find(tab => tab.id === activeElegantTab)?.label} View
              </h3>
              <p className="text-gray-600">
                Elegant tabs feature smooth animated underlines that scale in from the center. 
                Perfect for sophisticated, modern interfaces.
              </p>
            </div>
          </MinimalTabContent>
        </section>

        {/* Modern Tabs - Gradient Line Effect */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Modern Tabs - Gradient Line</h2>
          <p className="text-gray-600 mb-4">Gradient line effect that appears on hover</p>
          
          <ModernTabs className="mb-6">
            {minimalTabs.map((tab) => (
              <ModernTabItem
                key={tab.id}
                id={tab.id}
                label={tab.label}
                active={activeModernTab === tab.id}
                onClick={() => setActiveModernTab(tab.id)}
              />
            ))}
          </ModernTabs>

          <MinimalTabContent active={true}>
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {minimalTabs.find(tab => tab.id === activeModernTab)?.label} Page
              </h3>
              <p className="text-gray-600">
                Modern tabs use gradient lines that create a sophisticated visual effect. 
                Perfect for contemporary, high-end applications.
              </p>
            </div>
          </MinimalTabContent>
        </section>

        {/* Usage Examples */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Usage Guidelines</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-3">When to Use Each Type</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><strong>Card Tabs:</strong> Main navigation, dashboard sections</li>
                <li><strong>Underline Tabs:</strong> Secondary navigation, content sections</li>
                <li><strong>Segmented Tabs:</strong> Data filtering, time periods</li>
                <li><strong>Pill Tabs:</strong> Compact interfaces, mobile navigation</li>
                <li><strong>Clean Tabs:</strong> No borders, pure typography focus</li>
                <li><strong>Subtle Tabs:</strong> Light background hover effects</li>
                <li><strong>Elegant Tabs:</strong> Animated underline effects</li>
                <li><strong>Modern Tabs:</strong> Gradient line effects</li>
              </ul>
            </div>
            
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Best Practices</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Use consistent tab styling across your application</li>
                <li>• Include icons for better visual hierarchy</li>
                <li>• Add badges for notifications or counts</li>
                <li>• Ensure proper accessibility with ARIA labels</li>
                <li>• Test on mobile devices for touch interactions</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default TabShowcase;
