# Langflow Prototype Specification

A comprehensive specification for creating visually accurate prototypes of the Langflow application using tools like Lovable or V0.

## Table of Contents

1. [Application Layout Structure](#application-layout-structure)
2. [Visual Design Tokens](#visual-design-tokens)
3. [Page Templates & Layouts](#page-templates--layouts)
4. [Navigation & User Flows](#navigation--user-flows)
5. [Visual Assets & Iconography](#visual-assets--iconography)
6. [Interactive States & Behaviors](#interactive-states--behaviors)
7. [Responsive Design Specifications](#responsive-design-specifications)
8. [Component Usage Examples](#component-usage-examples)
9. [Animation & Transition Specs](#animation--transition-specs)
10. [Prototype Implementation Guide](#prototype-implementation-guide)

## Application Layout Structure

### Core Layout Architecture

Langflow uses a hierarchical layout system with consistent patterns across all pages:

```
App
├── Header (48px fixed height)
├── Main Content Area
│   ├── Sidebar (280px default, collapsible)
│   └── Content Panel (flex-1)
└── Modals/Overlays (Portal-based)
```

### Header Component Specification

**Dimensions**: Fixed height of 48px, full width
**Background**: Light: `bg-background`, Dark: `dark:bg-background`
**Border**: Bottom border `border-b`
**Padding**: `px-6` (24px horizontal)

#### Header Structure:
```tsx
// Left Section (Logo + Navigation)
<div className="flex shrink-0 items-center gap-2">
  <Button className="h-8 w-8 mr-1"> // Logo button
    {DATASTAX ? <DataStaxLogo /> : <LangflowLogo />}
  </Button>
  {/* Optional org/product selectors */}
</div>

// Center Section (Flow Menu)
<div className="absolute left-1/2 -translate-x-1/2">
  <FlowMenu />
</div>

// Right Section (Notifications + Account)
<div className="flex shrink-0 items-center gap-3">
  <Button> // Notification bell with badge
  <Separator orientation="vertical" className="h-7" />
  <AccountMenu />
</div>
```

### Sidebar Specification

**Default Width**: 280px for main navigation, 17.5rem (280px) for flow editor
**Background**: `bg-background` with `border-r`
**Collapsible**: Yes, with smooth animations
**Mobile Behavior**: Hidden by default, overlays content when open

#### Sidebar States:
- **Expanded**: Full width with text labels
- **Collapsed**: Icon-only view (64px width)
- **Mobile**: Overlay mode with backdrop

### Main Content Area

**Layout**: Flexbox container with `flex-1`
**Overflow**: `overflow-hidden` on container, `overflow-y-auto` on content
**Padding**: `p-4` (16px) for standard content areas
**Max Width**: `3xl:container` for large screens (1500px)

## Visual Design Tokens

### Precise Measurements

#### Spacing Scale (Tailwind + Custom)
- **Micro**: 2px (`0.5`)
- **Small**: 4px (`1`), 6px (`1.5`), 8px (`2`)
- **Medium**: 12px (`3`), 16px (`4`), 20px (`5`), 24px (`6`)
- **Large**: 32px (`8`), 40px (`10`), 44px (`11`), 48px (`12`)

#### Typography Scale
- **text-xxs**: 11px (Custom size for micro text)
- **text-xs**: 12px (Labels, captions)
- **text-mmd**: 13px (Custom intermediate size)
- **text-sm**: 14px (Body text, most UI)
- **text-base**: 16px (Card titles, form labels)
- **text-lg**: 18px (Dialog titles)

#### Border Radius System
- **sm**: `calc(var(--radius) - 4px)` ≈ 4px
- **md**: `calc(var(--radius) - 2px)` ≈ 6px
- **lg**: `var(--radius)` ≈ 8px
- **full**: 9999px (Pills, badges)

#### Shadow System
```css
/* Custom shadows from tailwind.config.mjs */
shadow-node: "0 0px 15px -3px rgb(0 0 0 / 0.1), 0 0px 6px -4px rgb(0 0 0 / 0.1)"
shadow-frozen-ring: "0 0 10px 2px rgba(128, 190, 230, 0.5)"
shadow-frosted-ring: "0 0 10px 2px rgba(128, 190, 230, 0.7)"
```

### Color Usage Patterns

#### Background Hierarchy
1. **App Background**: `bg-background` (white/dark)
2. **Content Areas**: `bg-background` or `bg-muted` (light gray/dark gray)
3. **Cards**: `bg-muted` with `border` and `shadow-sm`
4. **Inputs**: `bg-background` with `border-input`

#### Text Hierarchy
1. **Primary Text**: `text-foreground` (black/white)
2. **Secondary Text**: `text-muted-foreground` (gray)
3. **Placeholder Text**: `text-placeholder-foreground` (lighter gray)
4. **Links**: `text-primary` with `hover:underline`

#### Interactive States
- **Hover**: Subtle background change (`hover:bg-accent`)
- **Active/Selected**: `bg-accent` or accent color backgrounds
- **Focus**: `ring-2 ring-ring ring-offset-2`
- **Disabled**: `opacity-50` or `disabled:opacity-70`

## Page Templates & Layouts

### 1. Dashboard/Home Page Layout

```tsx
<SidebarProvider width="280px">
  <SideBarFoldersButtonsComponent />
  <main className="flex h-full w-full overflow-hidden">
    <div className="relative mx-auto flex h-full w-full flex-col overflow-hidden">
      <div className="flex h-full w-full flex-col 3xl:container">
        <CustomBanner /> {/* Optional top banner */}
        <div className="flex flex-1 flex-col justify-start p-4">
          <HeaderComponent /> {/* Page header with filters/search */}
          
          {/* Grid/List Toggle View */}
          {view === "grid" ? (
            <div className="mt-4 grid grid-cols-1 gap-1 md:grid-cols-2 lg:grid-cols-3">
              {/* Flow/Component cards */}
            </div>
          ) : (
            <div className="mt-4 flex flex-col gap-1">
              {/* Flow/Component list items */}
            </div>
          )}
          
          {/* Pagination */}
          <div className="flex justify-end px-3 py-4">
            <PaginatorComponent />
          </div>
        </div>
      </div>
    </div>
  </main>
</SidebarProvider>
```

**Visual Characteristics**:
- Sidebar with project folders and navigation
- Main content with 3-column grid on large screens
- Card-based layout with consistent spacing
- Pagination at bottom right

### 2. Flow Editor Layout

```tsx
<div className="flow-page-positioning">
  <div className="flex h-full overflow-hidden">
    <SidebarProvider width="17.5rem" defaultOpen={!isMobile}>
      <FlowSidebarComponent /> {/* Component palette */}
      <main className="flex w-full overflow-hidden">
        <div className="h-full w-full">
          {/* React Flow canvas */}
          <Page setIsLoading={setIsLoading} />
        </div>
      </main>
    </SidebarProvider>
  </div>
</div>
```

**Visual Characteristics**:
- Left sidebar with component palette (280px)
- Full-width canvas area
- Floating toolbar and controls
- Node-based visual editor

### 3. Settings Page Layout

```tsx
<div className="flex h-full">
  <aside className="w-64 border-r bg-background p-4">
    {/* Settings navigation */}
  </aside>
  <main className="flex-1 overflow-y-auto p-6">
    {/* Settings content */}
  </main>
</div>
```

## Navigation & User Flows

### Primary Navigation Structure

```
App Root
├── Dashboard (/)
│   ├── Flows (/flows)
│   ├── Components (/components) 
│   ├── All (/all)
│   └── MCP (/mcp)
├── Flow Editor (/flow/:id)
│   ├── Edit Mode (default)
│   └── View Mode (/flow/:id/view)
├── Settings (/settings)
│   ├── General (/settings/general)
│   ├── API Keys (/settings/api-keys)
│   ├── Global Variables (/settings/global-variables)
│   └── MCP Servers (/settings/mcp-servers)
└── Admin (/admin) [Protected]
```

### User Flow Patterns

#### 1. Dashboard Navigation
- Default redirect to `/flows`
- Tab switching between Flows/Components/MCP
- Grid/List view toggle (persistent in localStorage)
- Folder navigation in sidebar

#### 2. Flow Creation Flow
1. Click "New Flow" → Modal opens
2. Choose template or start blank
3. Navigate to `/flow/:id`
4. Auto-save enabled with visual indicators

#### 3. Settings Navigation
- Left sidebar navigation
- Each section has its own route
- Form-based interfaces with save/cancel patterns

## Visual Assets & Iconography

### Logo Assets

Located in `/src/assets/`:

#### Primary Logos
- **LangflowLogo.svg**: Standard white logo (24px × 24px in header)
- **LangflowLogoColor.svg**: Color version for light backgrounds
- **DataStaxLogo.svg**: Alternative logo for DataStax variant
- **langflow_logo_black.svg**: Black variant for light backgrounds
- **langflow_logo_white.svg**: White variant for dark backgrounds

#### Usage Context
- **Header Logo**: 24px × 24px, clickable, navigates to home
- **Loading Screens**: Larger versions (48px+)
- **Brand Contexts**: Color logos on neutral backgrounds

### Icon System

#### Icon Specifications
- **Primary Size**: 16px × 16px (`h-4 w-4`)
- **Secondary Size**: 20px × 20px (`h-5 w-5`)
- **Large Size**: 24px × 24px (`h-6 w-6`)
- **Stroke Width**: 1.5px (default), 2px (emphasis)

#### Common Icons & Context
```tsx
// Navigation & Actions
<Icon name="Settings" className="h-4 w-4" />
<Icon name="Bell" className="h-4 w-4" /> // Notifications
<Icon name="ChevronDown" className="h-4 w-4" /> // Dropdowns
<Icon name="Search" className="h-4 w-4" /> // Search inputs
<Icon name="Plus" className="h-4 w-4" /> // Add/Create actions

// File & Data Operations  
<Icon name="Download" className="h-4 w-4" />
<Icon name="Upload" className="h-4 w-4" />
<Icon name="Copy" className="h-4 w-4" />
<Icon name="Trash2" className="h-4 w-4" />

// UI States
<Icon name="Eye" className="h-4 w-4" /> // View mode
<Icon name="EyeOff" className="h-4 w-4" /> // Hidden
<Icon name="Check" className="h-4 w-4" /> // Success/Selected
<Icon name="X" className="h-4 w-4" /> // Close/Cancel
<Icon name="Loader2" className="h-4 w-4 animate-spin" /> // Loading
```

### Illustrations & Graphics

#### Empty States
- **undraw_design_components_9vy6.svg**: Component creation
- **undraw_chat_bot_re_e2gj.svg**: Chat/AI contexts
- **undraw_project_completed_re_jr7u.svg**: Completed states

#### Background Patterns
- **temp-pat-1.png**, **temp-pat-2.png**, **temp-pat-3.png**: Template backgrounds
- **memory-chatbot-bg.png**: Chat interface backgrounds
- **vector-rag-bg.png**: RAG/vector search contexts

#### Profile & Avatar
- **profile-circle.png**: Default user avatar
- **male-technologist.png**: User representation in empty states

## Interactive States & Behaviors

### Button States

#### Primary Button States
```tsx
// Default state
className="bg-primary text-primary-foreground hover:bg-primary-hover"

// Loading state (with spinner)
<Button loading={true}>
  <Loader2 className="h-4 w-4 animate-spin" />
  <span className="ml-2">Processing...</span>
</Button>

// Disabled state
className="disabled:opacity-70 disabled:pointer-events-none"

// Focus state
className="focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
```

### Form Input States

#### Input Field States
```tsx
// Default state
className="border border-input hover:bg-input"

// Focus state (floating label)
className="focus:ring-2 focus:ring-ring focus:border-primary"

// Error state
className="border-destructive ring-destructive"

// With icon
<div className="relative">
  <Icon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
  <Input className="pl-9" />
</div>
```

### Card Hover Effects
```tsx
// Interactive card
className="transition-all hover:shadow-md hover:border-accent"

// Selected state
className="border-primary bg-accent/10"
```

### Loading States

#### Page Loading
```tsx
<div className="flex h-full w-full items-center justify-center">
  <CustomLoader remSize={30} />
</div>
```

#### Component Loading (Skeleton)
```tsx
<div className="mt-4 flex flex-col gap-1">
  <Skeleton className="h-20 w-full" />
  <Skeleton className="h-20 w-full" />
</div>
```

## Responsive Design Specifications

### Breakpoint Behavior

#### Layout Adaptations
```css
/* Mobile (< 640px) */
- Sidebar: Hidden by default, overlay when open
- Grid: Single column
- Header: Compact with hamburger menu
- Padding: Reduced to p-2 (8px)

/* Tablet (640px - 1024px) */
- Sidebar: Collapsible, icons + labels
- Grid: 2 columns
- Header: Full navigation visible

/* Desktop (1024px+) */
- Sidebar: Full width by default
- Grid: 3 columns (lg:grid-cols-3)
- Header: All elements visible

/* Large (1200px+) */
- Container: Max-width constraints
- Grid: Maintains 3 columns with larger gaps
```

#### Component Responsive Patterns
```tsx
// Grid responsive classes
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3"

// Conditional rendering
{isMobile ? <MobileComponent /> : <DesktopComponent />}

// Responsive sidebar
<SidebarProvider defaultOpen={!isMobile}>
```

## Component Usage Examples

### Card Component Examples

#### Flow Card
```tsx
<Card className="group cursor-pointer transition-all hover:shadow-md">
  <CardHeader className="pb-2">
    <div className="flex items-center justify-between">
      <CardTitle className="text-sm font-medium">Flow Name</CardTitle>
      <Badge variant="successStatic">Active</Badge>
    </div>
    <CardDescription className="text-xs text-muted-foreground">
      Last modified 2 hours ago
    </CardDescription>
  </CardHeader>
  <CardContent className="pt-2">
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Icon name="Calendar" className="h-3 w-3" />
      <span>Created Jan 15, 2024</span>
    </div>
  </CardContent>
</Card>
```

#### Dashboard Stats Card
```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between pb-2">
    <CardTitle className="text-sm font-medium">Total Flows</CardTitle>
    <Icon name="Workflow" className="h-4 w-4 text-muted-foreground" />
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">24</div>
    <p className="text-xs text-muted-foreground">
      +2 from last month
    </p>
  </CardContent>
</Card>
```

### Form Layout Examples

#### Settings Form
```tsx
<form className="space-y-6">
  <div className="space-y-2">
    <Label htmlFor="name">Display Name</Label>
    <Input id="name" placeholder="Enter your name" />
  </div>
  
  <div className="space-y-2">
    <Label htmlFor="email">Email</Label>
    <Input id="email" type="email" placeholder="your@email.com" />
  </div>
  
  <div className="flex justify-end gap-2">
    <Button variant="outline">Cancel</Button>
    <Button>Save Changes</Button>
  </div>
</form>
```

#### Search Header
```tsx
<div className="flex items-center justify-between gap-4 p-4">
  <div className="flex items-center gap-2">
    <h2 className="text-lg font-semibold">Flows</h2>
    <Badge variant="secondary">{totalCount}</Badge>
  </div>
  
  <div className="flex items-center gap-2">
    <Input 
      placeholder="Search flows..." 
      icon="Search"
      className="w-64"
    />
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          <Icon name="Filter" className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
    </DropdownMenu>
    <Button>
      <Icon name="Plus" className="h-4 w-4 mr-2" />
      New Flow
    </Button>
  </div>
</div>
```

## Animation & Transition Specs

### Page Transitions
```css
/* Modal entrance */
.animate-in.fade-in-0.zoom-in-95.slide-in-from-bottom-2

/* Modal exit */
.animate-out.fade-out-0.zoom-out-95.slide-out-to-top-2

/* Content state changes */
.transition-all.duration-200
```

### Hover Animations
```css
/* Button hover */
.transition-colors.hover:bg-accent

/* Card hover */
.transition-all.hover:shadow-md.hover:border-accent

/* Icon hover */
.transition-colors.text-muted-foreground.hover:text-primary
```

### Loading Animations
```tsx
// Spinner animation
<Loader2 className="h-4 w-4 animate-spin" />

// Pulse effect
<div className="animate-pulse bg-muted h-4 w-full rounded" />

// Progressive loading
<div className="animate-in fade-in-0 duration-300 delay-[200ms]" />
```

## Prototype Implementation Guide

### For Lovable/V0 Development

#### 1. Project Structure Setup
```
src/
├── components/
│   ├── ui/           # Base components (Button, Input, Card, etc.)
│   ├── layout/       # Header, Sidebar, PageLayout
│   └── features/     # Page-specific components
├── pages/
│   ├── dashboard/    # Home/Dashboard pages
│   ├── flow-editor/  # Flow editing interface
│   └── settings/     # Settings pages
├── assets/
│   ├── icons/        # SVG icons
│   └── images/       # Illustrations and backgrounds
└── styles/
    └── globals.css   # Tailwind + CSS variables
```

#### 2. Essential CSS Variables
```css
:root {
  --background: 0 0% 100%;
  --foreground: 0 0% 0%;
  --muted: 240 5% 96%;
  --muted-foreground: 240 4% 46%;
  --primary: 0 0% 0%;
  --primary-foreground: 0 0% 100%;
  --border: 240 6% 90%;
  --input: 240 6% 90%;
  --ring: 0 0% 0%;
  --radius: 0.5rem;
}

.dark {
  --background: 240 6% 10%;
  --foreground: 0 0% 100%;
  --muted: 240 4% 16%;
  --muted-foreground: 240 5% 65%;
  --border: 240 5% 26%;
  --input: 240 5% 34%;
  --ring: 0 0% 100%;
}
```

#### 3. Component Priority Order
1. **Base UI Components**: Button, Input, Card, Badge (highest visual impact)
2. **Layout Components**: Header, Sidebar, PageLayout
3. **Navigation**: Menu, Tabs, Breadcrumbs
4. **Data Display**: Table, List, Grid components
5. **Forms**: Field groups, validation states
6. **Modals & Overlays**: Dialog, Popover, Tooltip

#### 4. Visual Accuracy Checklist

##### Layout Accuracy
- [ ] Header height exactly 48px
- [ ] Sidebar width 280px (collapsible)
- [ ] Consistent padding (p-4 = 16px)
- [ ] Proper flex layouts with overflow handling
- [ ] Grid responsive: 1/2/3 columns on mobile/tablet/desktop

##### Component Accuracy  
- [ ] Button heights: 32px (sm), 36px (sm), 40px (default), 44px (lg)
- [ ] Icon sizes: 16px default, 20px secondary, 24px large
- [ ] Border radius: 8px default (`rounded-lg`)
- [ ] Typography: Inter font, proper size scale
- [ ] Color usage matches semantic tokens

##### Interactive Accuracy
- [ ] Hover states on all interactive elements
- [ ] Focus rings with 2px offset
- [ ] Loading states with spinners
- [ ] Disabled states with 50-70% opacity
- [ ] Smooth transitions (200ms default)

##### Visual Polish
- [ ] Proper shadows on cards and modals
- [ ] Consistent spacing between elements
- [ ] Icon alignment and consistency
- [ ] Badge positioning and sizing
- [ ] Empty state illustrations

#### 5. Data Layer Mockup
```typescript
// Mock data structures for prototype
interface Flow {
  id: string;
  name: string;
  description: string;
  updated_at: string;
  is_component: boolean;
  folder_id: string;
}

interface User {
  name: string;
  email: string;
  avatar?: string;
}

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
}
```

### Success Metrics for Prototype

A visually accurate prototype should achieve:

1. **Layout Fidelity**: 95%+ match to actual component spacing and proportions
2. **Color Accuracy**: Exact match to CSS variable values
3. **Typography Match**: Correct font sizes, weights, and line heights  
4. **Interactive States**: All hover, focus, and disabled states present
5. **Responsive Behavior**: Proper breakpoint behavior across devices
6. **Performance**: Smooth animations and transitions
7. **Accessibility**: Proper focus management and semantic HTML

This specification provides the detailed visual and interaction requirements needed to create a prototype that closely matches the actual Langflow application. Use it as a reference guide throughout the prototyping process to ensure visual accuracy and consistent user experience.