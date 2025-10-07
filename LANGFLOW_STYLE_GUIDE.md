# Langflow Frontend Style Guide

This comprehensive style guide documents the design system for the Langflow frontend application, based on analysis of the React/TypeScript codebase with Tailwind CSS.

## Color Palette

### Primary Colors
- **Primary Black** - `hsl(0, 0%, 0%)` (Used for primary buttons, text, and emphasis)
- **Primary White** - `hsl(0, 0%, 100%)` (Used for backgrounds and button text)

### Semantic Colors
#### Success Colors
- **Success Background** - `hsl(149, 80%, 90%)` / Dark: `hsl(164, 86%, 16%)`
- **Success Foreground** - `hsl(161, 94%, 30%)` / Dark: `hsl(158, 64%, 52%)`
- **Status Green** - `var(--status-green)` (#4ade80)

#### Error/Destructive Colors  
- **Destructive** - `hsl(0, 72%, 51%)` / Dark: `hsl(0, 84%, 60%)`
- **Destructive Foreground** - `hsl(0, 0%, 100%)`
- **Error Background** - `#fef2f2` / Dark: `#450a0a`
- **Error Foreground** - `#991b1b` / Dark: `#fef2f2`
- **Status Red** - `var(--status-red)` (#ef4444)

#### Warning Colors
- **Warning** - `hsl(48, 96.6%, 76.7%)`
- **Warning Foreground** - `hsl(240, 6%, 10%)`
- **Warning Text** - `hsl(0, 0%, 100%)`
- **Status Yellow** - `var(--status-yellow)` (#eab308)

#### Info Colors
- **Info Background** - `#f0f4fd` / Dark: `#172554`
- **Info Foreground** - `#141653` / Dark: `#eff6ff`
- **Status Blue** - `var(--status-blue)` (#2563eb)

### Accent Colors
- **Accent Emerald** - `hsl(149, 80%, 90%)` / Dark: `hsl(164, 86%, 16%)`
- **Accent Pink** - `hsl(326, 78%, 95%)` / Dark: `hsl(336, 69%, 30%)`
- **Accent Indigo** - `hsl(226, 100%, 94%)` / Dark: `hsl(242, 25%, 34%)`
- **Accent Amber** - `hsl(48, 96%, 89%)` / Dark: `hsl(22, 78%, 26%)`

### Neutral Colors
- **Background** - `hsl(0, 0%, 100%)` / Dark: `hsl(240, 6%, 10%)`
- **Foreground** - `hsl(0, 0%, 0%)` / Dark: `hsl(0, 0%, 100%)`
- **Muted** - `hsl(240, 5%, 96%)` / Dark: `hsl(240, 4%, 16%)`
- **Muted Foreground** - `hsl(240, 4%, 46%)` / Dark: `hsl(240, 5%, 65%)`
- **Border** - `hsl(240, 6%, 90%)` / Dark: `hsl(240, 5%, 26%)`
- **Input** - `hsl(240, 6%, 90%)` / Dark: `hsl(240, 5%, 34%)`
- **Placeholder Foreground** - `hsl(240, 5%, 65%)` / Dark: `hsl(240, 4%, 46%)`

### Data Visualization Colors
- **Datatype Yellow** - `hsl(40.6, 96.1%, 40.4%)`
- **Datatype Blue** - `hsl(221.2, 83.2%, 53.3%)`  
- **Datatype Gray** - `hsl(215, 13.8%, 34.1%)`
- **Datatype Lime** - `hsl(84.8, 85.2%, 34.5%)`
- **Datatype Red** - `hsl(0, 72.2%, 50.6%)`
- **Datatype Violet** - `hsl(262.1, 83.3%, 57.8%)`
- **Datatype Emerald** - `hsl(161.4, 93.5%, 30.4%)`
- **Datatype Fuchsia** - `hsl(293.4, 69.5%, 48.8%)`
- **Datatype Purple** - `hsl(271.5, 81.3%, 55.9%)`
- **Datatype Cyan** - `hsl(191.6, 91.4%, 36.5%)`
- **Datatype Indigo** - `hsl(243.4, 75.4%, 58.6%)`

### Special Purpose Colors
- **Canvas** - `hsl(240, 5%, 96%)` / Dark: `hsl(0, 0%, 0%)`
- **Canvas Dot** - `hsl(240, 5%, 65%)` / Dark: `hsl(240, 5.3%, 26.1%)`
- **Node Selected** - `hsl(243, 75%, 59%)` / Dark: `hsl(234, 89%, 74%)`
- **Connection** - `var(--connection)` (#555 / #6d6c6c)
- **Ice** - `var(--ice)` (#31a3cc / #60a5fa)
- **Selected** - `var(--selected)` (#2196f3 / #0369a1)

## Typography

### Font Family
- **Primary Font**: Inter (CSS variable: `var(--font-sans)`)
- **Monospace Font**: JetBrains Mono (CSS variable: `var(--font-mono)`)  
- **Alternative Font**: Chivo (CSS variable: `var(--font-chivo)`)

### Font Weights
- Regular: 400
- Medium: 500  
- Semibold: 600
- Bold: 700

### Text Styles

#### Headings
- **Card Title**: `text-base font-semibold leading-tight tracking-tight` (16px)
  - Used for card headers and section titles
- **Alert Title**: `mb-1 font-medium leading-none tracking-tight`
  - Used for alert and notification headers

#### Body Text
- **Body**: `text-sm` (14px)
  - Standard text for most UI elements
- **Small**: `text-xs` (12px)
  - Used for secondary information and metadata
- **Extra Small**: `text-xxs` (11px)
  - Used for micro text and labels
- **Medium**: `text-mmd` (13px)  
  - Used for intermediate text sizing

#### Specialized Text
- **Card Description**: `text-sm text-muted-foreground`
  - Used for secondary descriptive text in cards
- **Alert Description**: `text-sm [&_p]:leading-relaxed`
  - Used for alert content with relaxed line height
- **Placeholder**: `text-placeholder-foreground`
  - Used for input placeholder text

## Component Styling

### Buttons

#### Base Button Classes
```css
/* Core button classes */
.noflow.nopan.nodelete.nodrag.inline-flex.items-center.justify-center.gap-2.whitespace-nowrap.rounded-md.text-sm.font-medium.ring-offset-background.transition-colors.focus-visible:outline-none.focus-visible:ring-1.focus-visible:ring-ring.focus-visible:ring-offset-2.disabled:opacity-70.disabled:pointer-events-none
```

#### Button Variants
- **Default**: `bg-primary text-primary-foreground hover:bg-primary-hover`
- **Destructive**: `bg-destructive text-destructive-foreground hover:bg-destructive/90`
- **Outline**: `border border-input hover:bg-input hover:text-accent-foreground`
- **Primary**: `border bg-background text-secondary-foreground hover:bg-muted hover:shadow-sm`
- **Secondary**: `border border-muted bg-muted text-secondary-foreground hover:bg-secondary-foreground/5`
- **Ghost**: `text-foreground hover:bg-accent hover:text-accent-foreground disabled:!bg-transparent`
- **Warning**: `bg-warning-foreground text-warning-text hover:bg-warning-foreground/90 hover:shadow-sm`

#### Button Sizes
- **Default**: `h-10 py-2 px-4` (40px height)
- **Medium**: `h-8 py-2 px-4` (32px height)
- **Small**: `h-9 px-3 rounded-md` (36px height)
- **Extra Small**: `py-0.5 px-3 rounded-md`
- **Large**: `h-11 px-8 rounded-md` (44px height)
- **Icon**: `p-1 rounded-md` (square icon button)
- **Icon Medium**: `p-1.5 rounded-md`
- **Icon Small**: `p-0.5 rounded-md`

### Cards

#### Base Card
```css
.flex.flex-col.justify-between.rounded-lg.border.bg-muted.text-card-foreground.shadow-sm.transition-all
```

#### Card Structure
- **Card Header**: `flex flex-col space-y-1.5 p-4` (16px padding)
- **Card Content**: `p-4 pt-0` (16px horizontal/bottom, no top)
- **Card Footer**: `flex items-center p-4 pt-0` (16px horizontal/bottom, no top)

### Input Fields

#### Base Input Structure
```css
/* Container */
.relative.block.h-fit.w-full.text-sm

/* Input field */
.nopan.nodelete.nodrag.noflow.primary-input.!placeholder-transparent
```

#### Input with Icon
- Icon positioning: `pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground`
- Input padding with icon: `pl-9`
- Placeholder with icon: `left-9`

### Badges

#### Badge Variants
- **Default**: `bg-primary hover:bg-primary/80 border-transparent text-primary-foreground`
- **Gray**: `bg-border hover:bg-border/80 text-secondary-foreground`
- **Secondary**: `bg-secondary hover:bg-secondary/80 border-transparent text-secondary-foreground`
- **Emerald**: `bg-accent-emerald text-accent-emerald-foreground hover:bg-accent-emerald-hover border-0`
- **Pink Static**: `bg-accent-pink text-accent-pink-foreground border-0`
- **Success Static**: `bg-accent-emerald text-accent-emerald-foreground border-0`
- **Error Static**: `bg-error-background text-error-foreground border-0`

#### Badge Sizes
- **Small**: `h-4 text-xs` (16px height)
- **Medium**: `h-5 text-sm` (20px height) 
- **Large**: `h-6 text-base` (24px height)
- **Square**: `h-6 px-1.5 text-sm font-medium rounded-md`

### Checkboxes & Form Controls

#### Checkbox
```css
.peer.h-4.w-4.shrink-0.rounded-sm.border.border-muted-foreground.ring-offset-background.focus-visible:outline-none.focus-visible:ring-2.focus-visible:ring-ring.focus-visible:ring-offset-2.disabled:cursor-not-allowed.disabled:opacity-50.data-[state=checked]:border-primary.data-[state=checked]:bg-primary.data-[state=checked]:text-primary-foreground
```

#### Switch
```css  
.peer.inline-flex.h-6.w-11.shrink-0.cursor-pointer.items-center.rounded-full.border-2.border-transparent.px-0.5.transition-colors.focus-visible:outline-none.focus-visible:ring-2.focus-visible:ring-ring.focus-visible:ring-offset-2.focus-visible:ring-offset-background.disabled:cursor-not-allowed.disabled:opacity-50.data-[state=checked]:bg-primary.data-[state=unchecked]:bg-input
```

### Tabs & Navigation

#### Tab List
```css
.inline-flex.h-10.w-full.items-center.rounded-none.text-muted-foreground.focus-visible:border-none
```

#### Tab Trigger  
```css
.inline-flex.h-full.items-center.justify-center.whitespace-nowrap.px-3.py-1.5.text-sm.font-medium.transition-all.disabled:pointer-events-none.disabled:opacity-50.data-[state=active]:border-b-2.data-[state=active]:border-current.data-[state=active]:text-primary.data-[state=inactive]:hover:text-primary
```

### Alerts

#### Alert Structure
```css
.relative.w-full.rounded-lg.border.p-4.[&>svg~*]:pl-7.[&>svg+div]:translate-y-[-3px].[&>svg]:absolute.[&>svg]:left-4.[&>svg]:top-4.[&>svg]:text-foreground
```

#### Alert Variants
- **Default**: `bg-background text-foreground`
- **Destructive**: `border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive`

## Spacing System
Based on Tailwind's default spacing scale:

- **0.5**: 2px (0.125rem) - Micro spacing
- **1**: 4px (0.25rem) - Minimal spacing  
- **1.5**: 6px (0.375rem) - Small spacing
- **2**: 8px (0.5rem) - Small spacing
- **3**: 12px (0.75rem) - Medium-small spacing  
- **4**: 16px (1rem) - Standard component padding
- **5**: 20px (1.25rem) - Medium spacing
- **6**: 24px (1.5rem) - Medium spacing
- **8**: 32px (2rem) - Large spacing
- **10**: 40px (2.5rem) - Standard button height
- **11**: 44px (2.75rem) - Large button height  
- **12**: 48px (3rem) - Extra large spacing

## Motion & Animation

### Keyframe Animations

#### Overlay Animations
```css
@keyframes overlayShow {
  from: { opacity: 0 }
  to: { opacity: 1 }
}

@keyframes overlayHide {
  from: { opacity: 1 }
  to: { opacity: 0 }
}
```

#### Content Animations
```css
@keyframes contentShow {
  from: {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.95);
    clip-path: inset(50% 0);
    box-shadow: 0 4px 8px -2px rgba(0, 0, 0, 0.1);
  }
  to: {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
    clip-path: inset(0% 0);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  }
}
```

#### Utility Animations
```css
@keyframes wiggle {
  0%, 100%: { transform: scale(100%) }
  50%: { transform: scale(120%) }
}

@keyframes pulse-pink {
  0%, 100%: { background-color: hsla(var(--accent-pink), 1) }
  50%: { background-color: hsla(var(--accent-pink), 0.4) }
}
```

### Animation Classes
- **Overlay Show**: `animate-overlayShow` (400ms cubic-bezier(0.16, 1, 0.3, 1))
- **Overlay Hide**: `animate-overlayHide` (500ms cubic-bezier(0.16, 1, 0.3, 1))
- **Content Show**: `animate-contentShow` (400ms cubic-bezier(0.16, 1, 0.3, 1))
- **Content Hide**: `animate-contentHide` (500ms cubic-bezier(0.16, 1, 0.3, 1))
- **Wiggle**: `animate-wiggle` (150ms ease-in-out)
- **Slow Wiggle**: `animate-slow-wiggle` (500ms ease-in-out)
- **Pulse Pink**: `animate-pulse-pink` (2s linear infinite)

### Transition Classes
- **Default**: `transition-colors` - For color transitions
- **All**: `transition-all` - For comprehensive property transitions
- **Transform**: `transition-transform` - For transform animations

## Dark Mode Support

### Dark Mode Implementation
Langflow uses CSS class-based dark mode with the `.dark` class applied to the root element.

### Dark Mode Color Variables
All colors are defined with both light and dark variants using CSS custom properties:

```css
:root {
  --background: 0 0% 100%; /* Light mode */
}

.dark {
  --background: 240 6% 10%; /* Dark mode */
}
```

### Dark Mode Usage
Components automatically adapt to dark mode through the CSS variable system. No additional classes needed for most components.

## Accessibility Guidelines

### Focus States
- **Focus Ring**: `focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-2`
- **Focus Outline**: `focus-visible:outline-none` (custom ring replaces default outline)
- **Ring Color**: Uses `--ring` CSS variable (black in light mode, white in dark mode)

### Touch Targets
- **Minimum Size**: Most interactive elements use minimum 32px (h-8) to 40px (h-10) heights
- **Icon Buttons**: 16px (p-1) to 24px (p-1.5) padding for comfortable touch targets

### Color Contrast
- **Text Contrast**: Uses semantic color variables that meet WCAG contrast requirements
- **Interactive States**: Hover and focus states provide clear visual feedback
- **Disabled States**: `disabled:opacity-70` provides clear disabled indication

### Screen Readers
- **Alert Role**: Alert components include `role="alert"` attribute
- **Semantic HTML**: Components use appropriate semantic elements (h3, h5, etc.)

## Responsive Design Specifications

### Breakpoints
Based on Tailwind's default breakpoints with custom extensions:

- **sm**: 640px (mobile landscape)
- **md**: 768px (tablet)  
- **lg**: 1024px (desktop)
- **xl**: 1200px (large desktop) - Custom breakpoint
- **2xl**: 1400px (extra large) - Custom breakpoint
- **3xl**: 1500px (ultra wide) - Custom breakpoint

### Container Sizes
```css
.container {
  center: true;
  screens: {
    "2xl": "1400px";
    "3xl": "1500px";  
  }
}
```

### Responsive Patterns
- **Grid Layouts**: Use CSS Grid with responsive column counts
- **Flexible Layouts**: Components use flexbox for adaptive layouts
- **Responsive Typography**: Text sizes remain consistent across breakpoints
- **Responsive Spacing**: Spacing scales appropriately with container sizes

## UX Patterns

### Modal/Dialog Patterns
- **Overlay**: Semi-transparent backdrop with blur effect
- **Content Animation**: Scale and clip-path animation for modal appearance
- **Focus Management**: Automatic focus trapping within modal content
- **Escape Handling**: ESC key closes modals

### Loading States  
- **Button Loading**: Spinner replaces button content with `loading` prop
- **Skeleton Loading**: Placeholder content during data loading
- **Disabled States**: Clear visual indication with reduced opacity

### Error Display
- **Inline Errors**: Field-level validation messages
- **Alert Errors**: Page-level error notifications with destructive styling
- **Toast Notifications**: Temporary success/error messages

### Form Patterns
- **Floating Labels**: Placeholder text that moves above input on focus
- **Icon Indicators**: Visual icons for input types and states  
- **Validation States**: Color-coded borders and messages for validation
- **Loading States**: Disabled state during form submission

### Navigation Patterns
- **Tab Navigation**: Horizontal tabs with active state indication
- **Sidebar Navigation**: Collapsible sidebar with hierarchical structure
- **Breadcrumbs**: Path indication for deep navigation

### Data Visualization
- **Status Indicators**: Color-coded badges for different states
- **Progress Indicators**: Progress bars and loading animations
- **Data Tables**: Structured data display with sorting and filtering
- **Charts**: Consistent color palette across all visualizations

## Custom Utilities

### Scrollbar Styling
```css
.custom-scroll {
  &::-webkit-scrollbar { width: 8px; height: 8px; }
  &::-webkit-scrollbar-track { background-color: hsl(var(--muted)); }
  &::-webkit-scrollbar-thumb { background-color: hsl(var(--border)); border-radius: 999px; }
  &::-webkit-scrollbar-thumb:hover { background-color: hsl(var(--placeholder-foreground)); }
}
```

### Text Utilities
- **Scrollbar Hide**: `.scrollbar-hide` - Completely hides scrollbars
- **Truncate Multiline**: `.truncate-multiline` - 3-line text truncation
- **Truncate Double**: `.truncate-doubleline` - 2-line text truncation
- **Word Break**: `.word-break-break-word` - Aggressive word breaking

### Special Effects
- **Frosted Glass**: `bg-frosted-glass backdrop-blur-xs` 
- **Frozen Effect**: `bg-frozen-blue shadow-frozen-ring`
- **Node Shadow**: `shadow-node` - Special shadow for node components

### Focus Management  
```css
:focus-visible {
  outline: none !important;
  outline-offset: 0px !important;
}
```

This style guide provides comprehensive documentation for maintaining consistency across the Langflow frontend application. All components should adhere to these patterns and specifications for optimal user experience and maintainability.