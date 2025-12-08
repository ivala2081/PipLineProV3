import React from 'react';
import { 
  UnifiedCard, 
  UnifiedButton, 
  UnifiedBadge, 
  UnifiedInput,
  UnifiedTable,
  UnifiedSection,
  UnifiedGrid
} from './UnifiedComponent';
import { 
  Search, 
  Plus, 
  Settings, 
  User, 
  Bell, 
  Download,
  Edit,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';

// Style Guide Component to demonstrate unified design system
export const StyleGuide: React.FC = () => {
  const sampleData = [
    { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'pending' },
  ];

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { 
      key: 'status', 
      label: 'Status',
      render: (value: string) => (
        <UnifiedBadge 
          variant={value === 'active' ? 'success' : value === 'inactive' ? 'destructive' : 'warning'}
        >
          {value}
        </UnifiedBadge>
      )
    },
  ];

  return (
    <div className="min-h-screen bg-background p-8 space-y-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-foreground">
            PipLinePro Design System
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            A unified design system ensuring consistency across all components and sections
          </p>
        </div>

        {/* Color Palette */}
        <UnifiedSection
          title="Color Palette"
          description="Consistent color usage across the application"
        >
          <UnifiedGrid cols={4} gap="md">
            <UnifiedCard variant="outlined" size="sm">
              <div className="space-y-2">
                <div className="w-full h-16 bg-primary rounded-md"></div>
                <div className="text-sm font-medium">Primary</div>
                <div className="text-xs text-muted-foreground">#3b82f6</div>
              </div>
            </UnifiedCard>
            
            <UnifiedCard variant="outlined" size="sm">
              <div className="space-y-2">
                <div className="w-full h-16 bg-secondary rounded-md"></div>
                <div className="text-sm font-medium">Secondary</div>
                <div className="text-xs text-muted-foreground">#f1f5f9</div>
              </div>
            </UnifiedCard>
            
            <UnifiedCard variant="outlined" size="sm">
              <div className="space-y-2">
                <div className="w-full h-16 bg-green-600 rounded-md"></div>
                <div className="text-sm font-medium">Success</div>
                <div className="text-xs text-muted-foreground">#16a34a</div>
              </div>
            </UnifiedCard>
            
            <UnifiedCard variant="outlined" size="sm">
              <div className="space-y-2">
                <div className="w-full h-16 bg-destructive rounded-md"></div>
                <div className="text-sm font-medium">Destructive</div>
                <div className="text-xs text-muted-foreground">#ef4444</div>
              </div>
            </UnifiedCard>
          </UnifiedGrid>
        </UnifiedSection>

        {/* Typography */}
        <UnifiedSection
          title="Typography"
          description="Consistent text styling and hierarchy"
        >
          <div className="space-y-4">
            <div>
              <h1 className="text-4xl font-bold text-foreground">Heading 1</h1>
              <p className="text-sm text-muted-foreground">4xl / Bold / Primary text</p>
            </div>
            <div>
              <h2 className="text-3xl font-semibold text-foreground">Heading 2</h2>
              <p className="text-sm text-muted-foreground">3xl / Semibold / Primary text</p>
            </div>
            <div>
              <h3 className="text-2xl font-medium text-foreground">Heading 3</h3>
              <p className="text-sm text-muted-foreground">2xl / Medium / Primary text</p>
            </div>
            <div>
              <p className="text-base text-foreground">Body text - Regular paragraph text</p>
              <p className="text-sm text-muted-foreground">Base / Regular / Primary text</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Small text - Secondary information</p>
              <p className="text-xs text-muted-foreground">Sm / Regular / Muted text</p>
            </div>
          </div>
        </UnifiedSection>

        {/* Buttons */}
        <UnifiedSection
          title="Buttons"
          description="Consistent button styles and variants"
        >
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium mb-4">Variants</h4>
              <div className="flex flex-wrap gap-4">
                <UnifiedButton variant="primary" icon={<Plus className="w-4 h-4" />}>
                  Primary
                </UnifiedButton>
                <UnifiedButton variant="secondary">Secondary</UnifiedButton>
                <UnifiedButton variant="outline">Outline</UnifiedButton>
                <UnifiedButton variant="ghost">Ghost</UnifiedButton>
                <UnifiedButton variant="success" icon={<CheckCircle className="w-4 h-4" />}>
                  Success
                </UnifiedButton>
                <UnifiedButton variant="warning" icon={<AlertTriangle className="w-4 h-4" />}>
                  Warning
                </UnifiedButton>
                <UnifiedButton variant="destructive" icon={<Trash2 className="w-4 h-4" />}>
                  Destructive
                </UnifiedButton>
              </div>
            </div>
            
            <div>
              <h4 className="text-lg font-medium mb-4">Sizes</h4>
              <div className="flex flex-wrap items-center gap-4">
                <UnifiedButton size="sm">Small</UnifiedButton>
                <UnifiedButton size="md">Medium</UnifiedButton>
                <UnifiedButton size="lg">Large</UnifiedButton>
              </div>
            </div>
            
            <div>
              <h4 className="text-lg font-medium mb-4">States</h4>
              <div className="flex flex-wrap gap-4">
                <UnifiedButton>Normal</UnifiedButton>
                <UnifiedButton disabled>Disabled</UnifiedButton>
                <UnifiedButton loading>Loading</UnifiedButton>
              </div>
            </div>
          </div>
        </UnifiedSection>

        {/* Badges */}
        <UnifiedSection
          title="Badges"
          description="Status indicators and labels"
        >
          <div className="flex flex-wrap gap-4">
            <UnifiedBadge variant="default">Default</UnifiedBadge>
            <UnifiedBadge variant="secondary">Secondary</UnifiedBadge>
            <UnifiedBadge variant="success">Success</UnifiedBadge>
            <UnifiedBadge variant="warning">Warning</UnifiedBadge>
            <UnifiedBadge variant="destructive">Destructive</UnifiedBadge>
            <UnifiedBadge variant="info">Info</UnifiedBadge>
            <UnifiedBadge variant="outline">Outline</UnifiedBadge>
          </div>
        </UnifiedSection>

        {/* Inputs */}
        <UnifiedSection
          title="Form Elements"
          description="Consistent form input styling"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <UnifiedInput
                label="Email Address"
                placeholder="Enter your email"
                type="email"
                icon={<User className="w-4 h-4" />}
              />
              
              <UnifiedInput
                label="Search"
                placeholder="Search..."
                icon={<Search className="w-4 h-4" />}
              />
              
              <UnifiedInput
                label="Password"
                placeholder="Enter password"
                type="password"
              />
            </div>
            
            <div className="space-y-4">
              <UnifiedInput
                label="With Error"
                placeholder="This field has an error"
                error="This field is required"
              />
              
              <UnifiedInput
                label="Disabled"
                placeholder="This field is disabled"
                disabled
              />
              
              <UnifiedInput
                label="With Helper Text"
                placeholder="Enter your name"
                helperText="This will be displayed on your profile"
              />
            </div>
          </div>
        </UnifiedSection>

        {/* Cards */}
        <UnifiedSection
          title="Cards"
          description="Consistent card layouts and styling"
        >
          <UnifiedGrid cols={3} gap="md">
            <UnifiedCard
              header={{
                title: "Default Card",
                description: "Standard card with header and content"
              }}
              variant="default"
            >
              <p className="text-muted-foreground">
                This is a default card with standard styling and padding.
              </p>
            </UnifiedCard>
            
            <UnifiedCard
              header={{
                title: "Outlined Card",
                description: "Card with border emphasis"
              }}
              variant="outlined"
            >
              <p className="text-muted-foreground">
                This card uses the outlined variant for emphasis.
              </p>
            </UnifiedCard>
            
            <UnifiedCard
              header={{
                title: "Elevated Card",
                description: "Card with shadow elevation"
              }}
              variant="elevated"
            >
              <p className="text-muted-foreground">
                This card uses elevation for visual hierarchy.
              </p>
            </UnifiedCard>
          </UnifiedGrid>
        </UnifiedSection>

        {/* Tables */}
        <UnifiedSection
          title="Data Tables"
          description="Consistent table styling and layout"
        >
          <UnifiedTable
            data={sampleData}
            columns={columns}
            striped
            hover
          />
        </UnifiedSection>

        {/* Layout Examples */}
        <UnifiedSection
          title="Layout Examples"
          description="Common layout patterns using unified components"
        >
          <div className="space-y-6">
            <UnifiedCard
              header={{
                title: "Dashboard Stats",
                description: "Key performance indicators",
                actions: (
                  <UnifiedButton variant="outline" size="sm" icon={<Settings className="w-4 h-4" />}>
                    Settings
                  </UnifiedButton>
                )
              }}
            >
              <UnifiedGrid cols={4} gap="md">
                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">1,234</div>
                  <div className="text-sm text-muted-foreground">Total Users</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">$12,345</div>
                  <div className="text-sm text-muted-foreground">Revenue</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">98.5%</div>
                  <div className="text-sm text-muted-foreground">Uptime</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">567</div>
                  <div className="text-sm text-muted-foreground">Orders</div>
                </div>
              </UnifiedGrid>
            </UnifiedCard>
          </div>
        </UnifiedSection>
      </div>
    </div>
  );
};
