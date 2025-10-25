# Langflow Design System

A comprehensive documentation of the atomic components and design system used in the Langflow frontend application.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Atomic Components](#atomic-components)
3. [Composite Components](#composite-components)
4. [Domain-Specific Components](#domain-specific-components)
5. [Layout Components](#layout-components)
6. [Utility Components](#utility-components)
7. [Component Patterns](#component-patterns)

## Architecture Overview

The Langflow design system is built using:

- **Base Framework**: React 18+ with TypeScript
- **Styling**: Tailwind CSS with CSS variables for theming
- **Component Library**: Custom components built on Radix UI primitives
- **Icons**: Lucide React with custom icon loading system
- **Animations**: CSS transitions and custom keyframe animations
- **Accessibility**: WCAG compliant with proper ARIA attributes

### Design System Structure

```
components/
├── ui/                    # Atomic UI components
├── common/                # Shared utility components
├── core/                  # Application-specific components
└── authorization/         # Auth guard components
```

## Atomic Components

### Button Component

**Location**: `src/components/ui/button.tsx`

The primary interactive component with multiple variants and sizes.

#### Props Interface
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  loading?: boolean;
  unstyled?: boolean;
  ignoreTitleCase?: boolean;
  variant?: "default" | "destructive" | "outline" | "outlineAmber" | "primary" | "warning" | "secondary" | "ghost" | "ghostActive" | "menu" | "menu-active" | "link";
  size?: "default" | "md" | "sm" | "xs" | "lg" | "iconMd" | "icon" | "iconSm" | "node-toolbar";
}
```

#### Variants
- **default**: Primary black button with white text
- **destructive**: Red button for dangerous actions
- **outline**: Border-only button
- **primary**: Secondary style with border
- **secondary**: Muted background
- **ghost**: Transparent background
- **warning**: Orange/amber warning button

#### Sizes
- **default**: 40px height (h-10 py-2 px-4)
- **md**: 32px height (h-8 py-2 px-4)
- **sm**: 36px height (h-9 px-3)
- **lg**: 44px height (h-11 px-8)
- **icon**: Square icon button variants

#### Usage Examples
```tsx
// Primary action button
<Button variant="default">Save Changes</Button>

// Destructive action
<Button variant="destructive">Delete Item</Button>

// Loading state
<Button loading={isLoading}>Submit</Button>

// Icon button
<Button size="icon" variant="ghost">
  <Icon name="Settings" />
</Button>
```

### Input Component

**Location**: `src/components/ui/input.tsx`

Text input field with optional icon support and floating label pattern.

#### Props Interface
```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: string;
  inputClassName?: string;
  placeholder?: string;
}
```

#### Features
- Floating placeholder labels
- Icon integration with automatic padding
- Custom focus states
- Password field support
- Auto-complete disabled by default

#### Usage Examples
```tsx
// Basic input
<Input placeholder="Enter your name" />

// Input with icon
<Input icon="Search" placeholder="Search..." />

// Password input
<Input type="password" placeholder="Password" />
```

### Card Component

**Location**: `src/components/ui/card.tsx`

Container component for grouping related content.

#### Component Structure
```tsx
// Base card container
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter>
    {/* Footer actions */}
  </CardFooter>
</Card>
```

#### Styling
- **Base**: `rounded-lg border bg-muted shadow-sm transition-all`
- **Header**: `p-4 space-y-1.5`
- **Content**: `p-4 pt-0`
- **Footer**: `p-4 pt-0`

### Badge Component

**Location**: `src/components/ui/badge.tsx`

Small status indicator components.

#### Props Interface
```typescript
interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "gray" | "secondary" | "destructive" | "outline" | "secondaryStatic" | "pinkStatic" | "emerald" | "successStatic" | "errorStatic";
  size?: "sm" | "md" | "lg" | "sq" | "xq";
}
```

#### Variants
- **default**: Primary colored badge
- **gray**: Neutral gray badge
- **emerald**: Success/positive status
- **pinkStatic**: Pink accent badge
- **successStatic**: Success status
- **errorStatic**: Error status

#### Usage Examples
```tsx
<Badge variant="successStatic">Active</Badge>
<Badge variant="errorStatic">Failed</Badge>
<Badge size="sm" variant="emerald">New</Badge>
```

### Checkbox Component

**Location**: `src/components/ui/checkbox.tsx`

Boolean input control with custom styling.

#### Features
- Custom check mark icon
- Indeterminate state support
- Proper focus management
- Accessibility compliant

#### Usage Examples
```tsx
<Checkbox checked={isChecked} onCheckedChange={setIsChecked} />
<label>Accept terms and conditions</label>
```

### Switch Component

**Location**: `src/components/ui/switch.tsx`

Toggle switch for boolean values.

#### Styling
- **Track**: 44px width × 24px height
- **Thumb**: 20px diameter with 2px inner padding
- **Animation**: 150ms transform transition

#### Usage Examples
```tsx
<Switch checked={darkMode} onCheckedChange={setDarkMode} />
```

### Select Component

**Location**: `src/components/ui/select.tsx`

Dropdown selection component with search and multi-select support.

#### Component Structure
```tsx
<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select option..." />
  </SelectTrigger>
  <SelectContent>
    <SelectLabel>Options</SelectLabel>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectSeparator />
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

#### Features
- Chevron direction control
- Search functionality
- Group labels and separators
- Custom positioning

### Textarea Component

**Location**: `src/components/ui/textarea.tsx`

Multi-line text input field.

#### Props Interface
```typescript
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  password?: boolean;
  editNode?: boolean;
}
```

#### Features
- Auto-resize capability
- Password masking support
- Custom scrollbar styling
- Node editing context awareness

### Alert Component

**Location**: `src/components/ui/alert.tsx`

Contextual feedback and messaging component.

#### Component Structure
```tsx
<Alert variant="default">
  <AlertIcon />
  <AlertTitle>Alert Title</AlertTitle>
  <AlertDescription>
    Alert description text...
  </AlertDescription>
</Alert>
```

#### Variants
- **default**: Standard informational alert
- **destructive**: Error/warning alerts with red styling

## Composite Components

### Dialog Component

**Location**: `src/components/ui/dialog.tsx`

Modal dialog component with overlay and focus management.

#### Component Structure
```tsx
<Dialog>
  <DialogTrigger>Open Dialog</DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Dialog description</DialogDescription>
    </DialogHeader>
    {/* Content */}
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

#### Features
- Automatic focus trapping
- ESC key handling
- Backdrop click to close
- Accessibility compliant
- Custom close button with tooltip

### Dropdown Menu Component

**Location**: `src/components/ui/dropdown-menu.tsx`

Context menu component with multiple interaction patterns.

#### Component Structure
```tsx
<DropdownMenu>
  <DropdownMenuTrigger>
    <Button>Menu</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem>Item 1</DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuCheckboxItem checked={checked}>
      Checkbox Item
    </DropdownMenuCheckboxItem>
    <DropdownMenuRadioGroup value={value}>
      <DropdownMenuRadioItem value="option1">
        Radio Option 1
      </DropdownMenuRadioItem>
    </DropdownMenuRadioGroup>
  </DropdownMenuContent>
</DropdownMenu>
```

#### Features
- Nested sub-menus
- Checkbox and radio items
- Keyboard navigation
- Custom shortcuts display
- Inset options for hierarchy

### Popover Component

**Location**: `src/components/ui/popover.tsx`

Floating content container for contextual information.

#### Component Structure
```tsx
<Popover>
  <PopoverTrigger>
    <Button>Show Info</Button>
  </PopoverTrigger>
  <PopoverContent align="start" side="bottom">
    Popover content here...
  </PopoverContent>
</Popover>
```

#### Features
- Positioning control (side, align)
- Custom offset configuration
- Portal and non-portal variants
- Auto-dismiss behavior

### Tabs Component

**Location**: `src/components/ui/tabs.tsx`

Tab navigation component for content organization.

#### Component Structure
```tsx
<Tabs defaultValue="tab1">
  <TabsList>
    <TabsTrigger value="tab1">Tab 1</TabsTrigger>
    <TabsTrigger value="tab2">Tab 2</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">
    Content for tab 1
  </TabsContent>
  <TabsContent value="tab2">
    Content for tab 2
  </TabsContent>
</Tabs>
```

#### Features
- Keyboard navigation
- Active state indicators
- Horizontal scroll support
- Accessible tab panels

### Accordion Component

**Location**: `src/components/ui/accordion.tsx`

Collapsible content sections.

#### Component Structure
```tsx
<Accordion type="single" collapsible>
  <AccordionItem value="item1">
    <AccordionTrigger disabled={isEmpty}>
      Section Title
    </AccordionTrigger>
    <AccordionContent>
      Section content...
    </AccordionContent>
  </AccordionItem>
</Accordion>
```

#### Features
- Single or multiple expand modes
- Disabled state handling
- Custom animations
- Tooltip integration

### Table Component

**Location**: `src/components/ui/table.tsx`

Data table component with semantic HTML structure.

#### Component Structure
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Column 1</TableHead>
      <TableHead>Column 2</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Data 1</TableCell>
      <TableCell>Data 2</TableCell>
    </TableRow>
  </TableBody>
  <TableFooter>
    <TableRow>
      <TableCell colSpan={2}>Footer</TableCell>
    </TableRow>
  </TableFooter>
  <TableCaption>Table caption</TableCaption>
</Table>
```

#### Features
- Responsive design
- Hover states on rows
- Selection states
- Checkbox integration support

## Domain-Specific Components

### Generic Icon Component

**Location**: `src/components/common/genericIconComponent/index.tsx`

Dynamic icon loading system with fallback handling.

#### Props Interface
```typescript
interface IconComponentProps {
  name: string;
  className?: string;
  iconColor?: string;
  stroke?: string;
  strokeWidth?: number;
  id?: string;
  skipFallback?: boolean;
  dataTestId?: string;
}
```

#### Features
- Lazy icon loading with caching
- Dark mode awareness
- Error boundaries
- Fallback skeleton loader
- Custom stroke and color support

#### Usage Examples
```tsx
<ForwardedIconComponent name="Settings" className="h-5 w-5" />
<ForwardedIconComponent 
  name="Search" 
  iconColor="#FF0000"
  strokeWidth={2}
/>
```

### Loading Component

**Location**: `src/components/common/loadingComponent/index.tsx`

Animated loading indicator.

#### Props Interface
```typescript
interface LoadingComponentProps {
  remSize?: number;
}
```

#### Features
- SVG-based spinner animation
- Customizable size
- Accessible with proper ARIA attributes
- Primary color theming

### Node Components

**Location**: `src/CustomNodes/`

Specialized components for the flow editor:

#### GenericNode
- **Location**: `src/CustomNodes/GenericNode/index.tsx`
- **Purpose**: Base node component for flow editor
- **Features**: Drag handles, parameter rendering, validation status

#### NoteNode  
- **Location**: `src/CustomNodes/NoteNode/index.tsx`
- **Purpose**: Annotation nodes for flow documentation
- **Features**: Rich text editing, markdown support, resizable

### Parameter Render Components

**Location**: `src/components/core/parameterRenderComponent/components/`

Specialized input components for different data types:

- **FloatComponent**: Numeric inputs with validation
- **IntComponent**: Integer-only inputs
- **DropdownComponent**: Select inputs with custom options
- **TextAreaComponent**: Multi-line text inputs
- **SliderComponent**: Range input controls
- **ToggleShadComponent**: Boolean toggle controls
- **MultiselectComponent**: Multiple selection inputs
- **KeypairListComponent**: Key-value pair inputs
- **InputListComponent**: Dynamic list inputs

## Layout Components

### Page Layout

**Location**: `src/components/common/pageLayout/index.tsx`

Base page structure component providing consistent layout patterns.

### Sidebar Component  

**Location**: `src/components/ui/sidebar.tsx`

Navigation sidebar with collapsible sections.

### Scroll Area

**Location**: `src/components/ui/scroll-area.tsx`

Custom scrollable container with styled scrollbars.

## Utility Components

### Skeleton Component

**Location**: `src/components/ui/skeleton.tsx`

Loading placeholder component.

#### Usage
```tsx
<Skeleton className="h-4 w-full" />
<Skeleton className="h-8 w-8 rounded-full" />
```

### Progress Component

**Location**: `src/components/ui/progress.tsx`

Progress bar indicator.

#### Usage
```tsx
<Progress value={75} className="w-full" />
```

### Tooltip Component

**Location**: `src/components/ui/tooltip.tsx`

Contextual help and information display.

#### Component Structure
```tsx
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger>Hover me</TooltipTrigger>
    <TooltipContent>
      Helpful information
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

### Separator Component

**Location**: `src/components/ui/separator.tsx`

Visual divider component.

#### Usage
```tsx
<Separator orientation="horizontal" />
<Separator orientation="vertical" className="h-4" />
```

## Component Patterns

### Composition Pattern

Components are designed to be composable and follow the compound component pattern:

```tsx
// Example: Card composition
<Card>
  <CardHeader>
    <CardTitle>User Profile</CardTitle>
    <CardDescription>Manage your account settings</CardDescription>
  </CardHeader>
  <CardContent>
    <form>
      <Input placeholder="Name" />
      <Input placeholder="Email" />
    </form>
  </CardContent>
  <CardFooter>
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

### Variant Pattern

Components use class-variance-authority (CVA) for variant management:

```tsx
const buttonVariants = cva(
  "base-classes",
  {
    variants: {
      variant: {
        default: "variant-specific-classes",
        outline: "other-variant-classes",
      },
      size: {
        default: "size-specific-classes",
        sm: "small-size-classes",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

### Forward Ref Pattern

All components properly forward refs for integration with form libraries and parent components:

```tsx
const Component = React.forwardRef<HTMLElement, Props>(
  ({ className, ...props }, ref) => (
    <element
      ref={ref}
      className={cn("base-styles", className)}
      {...props}
    />
  )
);
Component.displayName = "Component";
```

### Accessibility Pattern

Components include proper ARIA attributes and keyboard navigation:

```tsx
<button
  role="button"
  aria-expanded={isOpen}
  aria-label="Close dialog"
  onKeyDown={handleKeyDown}
  tabIndex={0}
>
  Content
</button>
```

### Theming Pattern

All components respect the theme system through CSS variables:

```tsx
// Component uses semantic color variables
className="bg-background text-foreground border-border"

// Colors automatically switch in dark mode
.dark {
  --background: hsl(240, 6%, 10%);
  --foreground: hsl(0, 0%, 100%);
}
```

### Animation Pattern

Components use consistent animation patterns:

```tsx
// Entrance animations
className="animate-in fade-in-0 zoom-in-95 slide-in-from-bottom-2"

// Exit animations  
className="animate-out fade-out-0 zoom-out-95 slide-out-to-top-2"

// State transitions
className="transition-colors transition-transform hover:scale-105"
```

## Best Practices

### Component Usage
1. Always use the `cn()` utility for className merging
2. Forward refs for all interactive components
3. Include proper TypeScript interfaces
4. Use semantic HTML elements
5. Include data-testid attributes for testing

### Styling Guidelines
1. Use Tailwind utility classes primarily
2. Create CSS variables for theme-specific values
3. Follow the spacing scale (4px increments)
4. Use semantic color names instead of specific colors
5. Ensure proper contrast ratios for accessibility

### Performance Optimization
1. Lazy load icons and heavy components
2. Use React.memo for expensive re-renders
3. Implement proper error boundaries
4. Cache frequently used components
5. Optimize bundle size with code splitting

This design system provides a comprehensive foundation for building consistent, accessible, and maintainable user interfaces in the Langflow application.