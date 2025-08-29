# Complete LangBuilder Interface Nodes

Based on deep analysis of the frontend codebase, here are all the interface components with their complete details:

## Main Application Pages

### 1. LoginPage
**Route:** `/login`
**Components:**
- Form with username/password fields
- Sign In button with validation
- Link to Sign Up page
- Langflow logo display
- Error alert handling for authentication failures
**Features:**
- JWT token authentication
- Remember me functionality
- Redirect to dashboard after successful login

### 2. SignUpPage  
**Route:** `/signup`
**Components:**
- Registration form with username/password/confirm password
- Create Account button
- Link back to Login page
- Username availability checking
- Password strength requirements
**Features:**
- Real-time validation
- Auto-login after registration

### 3. FlowDashboard (HomePage)
**Route:** `/flows`, `/components`, `/all`, `/mcp`
**Components:**
- Header with search bar and view toggle (grid/list)
- Folder sidebar navigation
- Flow/Component cards with actions
- Pagination controls
- Empty state components
- Batch selection with Shift/Ctrl support
- Dropdown actions (duplicate, export, delete)
**Features:**
- Three tabs: Flows, Components, MCP Tools
- Folder-based organization
- Search and filter capabilities
- Drag-and-drop file upload
- Bulk operations on selected items

### 4. FlowEditor
**Route:** `/flow/:id`
**Components:**
- React Flow canvas with zoom/pan controls
- Sidebar with component library
- Toolbar with save/run/share/export actions
- Node editor modal for configuration
- Minimap for navigation
- Connection lines with validation
- Context menu for node operations
**Features:**
- Visual flow building with drag-and-drop
- Real-time validation
- Auto-save functionality
- Component search and filtering
- Undo/redo support
- Keyboard shortcuts

### 5. PlaygroundInterface (Chat)
**Route:** `/playground/:id`
**Components:**
- Chat window with message history
- Message input with file attachments
- Voice input button
- Session manager sidebar
- File preview components
- Typing indicators
- Message actions (copy, edit, delete)
**Features:**
- WebSocket-based real-time messaging
- Multi-session support
- File upload and preview
- Voice mode with transcription
- Message streaming
- Session persistence

### 6. SettingsPage
**Route:** `/settings/*`
**Subpages:**
- **GeneralPage** (`/settings/general`)
  - Profile picture upload
  - Password change form
  - Theme toggle (light/dark/system)
  - Account deletion option
- **GlobalVariablesPage** (`/settings/global-variables`)
  - Variable creation form
  - Environment variable management
  - Encrypted credential storage
- **ApiKeysPage** (`/settings/api-keys`)
  - API key generation
  - Key management table
  - Usage statistics
  - Key revocation
- **MCPServersPage** (`/settings/mcp-servers`)
  - MCP server configuration
  - Tool registration
  - Server status monitoring
- **ShortcutsPage** (`/settings/shortcuts`)
  - Keyboard shortcut customization
  - Command palette configuration
- **MessagesPage** (`/settings/messages`)
  - Message history viewer
  - Export functionality

### 7. AdminPage
**Route:** `/admin`
**Components:**
- User management table
- Role assignment interface
- System configuration panels
- Audit log viewer
**Features:**
- Protected route (requires superuser)
- User CRUD operations
- System-wide settings

### 8. ViewPage
**Route:** `/flow/:id/view`
**Components:**
- Read-only flow visualization
- Component details panel
- Export options
**Features:**
- Public/private flow viewing
- Share functionality

## Modal Components

### 1. IOModal (Playground Modal)
- Chat interface for flow testing
- Input/output field configuration
- Session management
- Real-time execution feedback

### 2. APIModal
- Code snippet generation (Python, JavaScript, cURL)
- Widget embedding code
- API endpoint documentation
- Authentication token display

### 3. ShareModal
- Public/private toggle
- Share link generation
- Access control settings
- Embed code generation

### 4. TemplatesModal
- Template gallery with categories
- Template preview
- One-click import
- Getting started guides

### 5. EditNodeModal
- Component parameter configuration
- Advanced settings toggle
- Input/output mapping
- Validation feedback

### 6. FileManagerModal
- File browser interface
- Drag-and-drop upload
- Recent files section
- File type filtering

### 7. FlowSettingsModal
- Flow metadata editing
- Icon and color selection
- Endpoint configuration
- Access type settings

### 8. GlobalVariableModal
- Variable creation/editing
- Type selection
- Default value configuration
- Scope settings

## Reusable UI Components

### Reusable Component Library

#### Core Navigation Components
- **CardComponent** (`src/components/common/cardComponent`): Flow/component display cards with metadata, actions, drag-and-drop
- **SidebarComponent** (`src/components/core/sidebarComponent`): Collapsible navigation with folder hierarchy
- **HeaderComponent** (`src/components/core/appHeaderComponent`): App header with user menu, theme toggle, navigation
- **PaginatorComponent** (`src/components/common/paginatorComponent`): Pagination with page size controls
- **SearchInput**: Debounced search with autocomplete suggestions
- **DropdownComponent** (`src/components/core/dropdownComponent`): Custom dropdown with keyboard navigation

#### Advanced Input Components
- **InputComponent** (`src/components/core/parameterRenderComponent/components/inputComponent`): 
  - Multi-mode support (text, password, dropdown, object selection)
  - Global variable integration
  - Validation feedback
  - Icon and button support
  - Custom popover for options
- **FloatComponent** / **IntComponent**: Numeric inputs with range validation
- **SliderComponent**: Range input with custom labels and preset buttons
- **TextAreaComponent**: Code editor integration, syntax highlighting
- **DropdownComponent**: Searchable, multi-select, with metadata display
- **FileInputComponent**: Drag-and-drop with preview, multiple file support

#### Data Display Components
- **JsonEditor** (`src/components/core/jsonEditor`): Monaco editor integration
- **CodeEditor**: Syntax highlighting, multiple language support
- **TableComponent**: Virtual scrolling, sorting, filtering, selection
- **ImageViewer** (`src/components/common/ImageViewer`): Zoom, pan, format support
- **DataOutputComponent**: Structured data rendering with type awareness
- **CsvOutputComponent**: Tabular data display with export

#### Specialized Components
- **ReactFlow Integration**: Custom nodes, edges, connection validation
- **ChatComponents**: Message display, file attachments, streaming support
- **NodeToolbar**: Context actions, parameter editing, status indicators
- **ParameterRender**: Dynamic form generation based on node schemas

## State Management Architecture

### Zustand Store System
**Global State Stores:**
1. **authStore** (`src/stores/authStore.ts`): 
   - User authentication state (login, logout, token refresh)
   - User profile data and permissions
   - Auto-login configuration

2. **flowStore** (`src/stores/flowStore.ts`):
   - Current flow data (nodes, edges, metadata)
   - Flow execution state and build status
   - Input/output field management
   - Real-time collaboration state

3. **flowsManagerStore** (`src/stores/flowsManagerStore.ts`):
   - Flow collection management (CRUD operations)
   - Flow templates and examples
   - Import/export functionality
   - Folder-based organization

4. **messagesStore** (`src/stores/messagesStore.ts`):
   - Chat message history and sessions
   - Message streaming state
   - File attachment management
   - Session persistence

5. **utilityStore** (`src/stores/utilityStore.ts`):
   - UI state (sidebar open/closed, view preferences)
   - Chat value store for real-time input
   - Playground scroll behavior
   - Client ID management
   - Current session tracking

6. **alertStore** (`src/stores/alertStore.ts`):
   - Toast notification queue
   - Error and success message display
   - Alert persistence and auto-dismiss

7. **foldersStore** (`src/stores/foldersStore.ts`):
   - Folder hierarchy and navigation
   - Folder CRUD operations
   - My Collection management

8. **typesStore** (`src/stores/typesStore.ts`):
   - Component type definitions
   - Category mappings and icons
   - Dynamic component loading

9. **globalVariablesStore**: Environment variable management
10. **darkStore** (`src/stores/darkStore.ts`): Theme preference persistence
11. **voiceStore** (`src/stores/voiceStore.ts`): Voice input settings and state
12. **storeStore** (`src/stores/storeStore.ts`): Component store integration
13. **tweaksStore** (`src/stores/tweaksStore.ts`): Flow parameter tweaking

## Navigation Patterns

### Protected Routes
- **ProtectedRoute**: Requires authentication
- **ProtectedAdminRoute**: Requires superuser role
- **ProtectedLoginRoute**: Redirects if already logged in
- **AuthSettingsGuard**: Checks auth provider settings

### User Flows
1. **Onboarding Flow**: Login → Dashboard → Create First Flow
2. **Flow Creation**: Dashboard → New Flow → Editor → Save
3. **Flow Testing**: Editor → Playground → Chat → Results
4. **Settings Flow**: Dashboard → Settings → Configure → Save
5. **Sharing Flow**: Flow → Share → Configure Access → Get Link

## Dynamic Content & Conditional Rendering

### Feature Flags
- `ENABLE_CUSTOM_PARAM`: Custom URL parameters
- `ENABLE_FILE_MANAGEMENT`: File management features
- `ENABLE_MCP`: MCP server integration
- `ENABLE_DATASTAX_LANGFLOW`: DataStax features
- `ENABLE_PROFILE_ICONS`: Profile customization

### Conditional UI Elements
- Admin menu items (based on user role)
- MCP tab (based on feature flag)
- File management (based on feature flag)
- Store integration (based on configuration)
- Voice mode (based on browser capabilities)

## Component Library Architecture

### UI Component System
**Base Components (Radix UI + Custom):**
- **Button**: Extensive variant system with 12 variants (default, destructive, outline, primary, etc.), 9 size options, loading states, title case conversion
- **Input**: Icon support, placeholder animation, password visibility toggle, form integration
- **Modal System**: BaseModal with trigger/content pattern, size variants (x-small to x-large), animation states
- **Form Components**: Radix UI Form integration with validation, custom styling

### Component Props & Interfaces

#### Page Component Patterns
```typescript
interface PageProps {
  type?: "flows" | "components" | "mcp"
  view?: "grid" | "list"
  folderId?: string
  isLoading?: boolean
}

interface IOModalPropsType {
  children: JSX.Element
  open: boolean
  setOpen: (open: boolean) => void
  disable?: boolean
  isPlayground?: boolean
  canvasOpen?: boolean
  playgroundPage?: boolean
}
```

#### Form Component Interfaces
```typescript
interface InputComponentType {
  name?: string
  autoFocus?: boolean
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void
  value?: string
  disabled?: boolean
  onChange?: (value: string, snapshot?: boolean) => void
  password: boolean
  required?: boolean
  isForm?: boolean
  editNode?: boolean
  placeholder?: string
  className?: string
  id?: string
  blurOnEnter?: boolean
  optionsIcon?: string
  optionsPlaceholder?: string
  options?: string[]
  selectedOption?: string
  setSelectedOption?: (value: string) => void
  selectedOptions?: string[]
  setSelectedOptions?: (value: string[]) => void
  objectOptions?: Array<{ name: string; id: string }>
  isObjectOption?: boolean
  nodeStyle?: boolean
  isToolMode?: boolean
  popoverWidth?: string
  commandWidth?: string
  blockAddNewGlobalVariable?: boolean
  hasRefreshButton?: boolean
}

interface DropDownComponent {
  disabled?: boolean
  isLoading?: boolean
  value: string
  combobox?: boolean
  nodeId: string
  nodeClass: APIClassType
  handleNodeClass: (value: any, code?: string, type?: string) => void
  options: string[]
  optionsMetaData?: any[]
  onSelect: (value: string, dbValue?: boolean, snapshot?: boolean) => void
  editNode?: boolean
  id?: string
  children?: ReactNode
  name: string
  dialogInputs?: any
  toggle?: boolean
}
```

#### Modal Component Interfaces
```typescript
interface ConfirmationModalType {
  onCancel?: () => void
  title: string
  titleHeader?: string
  destructive?: boolean
  destructiveCancel?: boolean
  modalContentTitle?: string
  loading?: boolean
  cancelText?: string
  confirmationText?: string
  children: [React.ReactElement<ContentProps>, React.ReactElement<TriggerProps>] | React.ReactElement<ContentProps>
  icon?: string
  data?: any
  index?: number
  onConfirm?: (index, data) => void
  open?: boolean
  onClose?: () => void
  size?: "x-small" | "smaller" | "small" | "medium" | "large" | "large-h-full" | "small-h-full" | "medium-h-full"
  onEscapeKeyDown?: (e: KeyboardEvent) => void
}
```

#### Chat Component Interfaces
```typescript
interface ChatInputType {
  isDragging: boolean
  files: FilePreviewType[]
  setFiles: (files: FilePreviewType[] | ((prev: FilePreviewType[]) => FilePreviewType[])) => void
  inputRef: { current: any }
  noInput: boolean
  sendMessage: ({ repeat, files }: { repeat: number; files?: string[] }) => Promise<void>
  playgroundPage: boolean
}

interface chatMessagePropsType {
  chat: ChatMessageType
  lastMessage: boolean
  updateChat: (chat: ChatMessageType, message: string, stream_url?: string) => void
  closeChat?: () => void
  playgroundPage?: boolean
}
```

#### Parameter Render Component Interfaces
```typescript
interface ParameterComponentType {
  selected?: boolean
  data: NodeDataType
  title: string
  conditionPath?: string | null
  key: string
  id: sourceHandleType | targetHandleType
  colors: string[]
  left: boolean
  type: string | undefined
  required?: boolean
  name?: string
  tooltipTitle: string | undefined
  optionalHandle?: Array<string> | null
  info?: string
  proxy?: { field: string; id: string }
  showNode?: boolean
  index: number
  onCloseModal?: (close: boolean) => void
  outputName?: string
  outputProxy?: OutputFieldProxyType
}
```

## Styling System & Theme Architecture

### Tailwind CSS Configuration
**Custom Design System:**
- **Color Palette**: 100+ custom CSS variables with HSL values for consistent theming
- **Gradient System**: 46 predefined gradients, 9 flow-specific gradients, theme-aware swatches
- **Animations**: Custom keyframes (overlayShow, contentShow, border-beam, pulse-pink)
- **Typography**: Custom font families (Chivo, Inter), extended font sizes
- **Spacing**: Custom border widths, extended z-index scale, backdrop blur utilities

### Color System Architecture
```css
:root {
  /* Primary Colors */
  --primary: 220 14% 96%;
  --primary-foreground: 220.9 39.3% 11%;
  --primary-hover: 210 40% 92%;
  
  /* Accent Colors */
  --accent-emerald: 142.1 76.2% 36.3%;
  --accent-pink: 330 81% 60%;
  --accent-purple: 262.1 83.3% 57.8%;
  
  /* Data Type Colors */
  --datatype-yellow: 47.9 95.8% 53.1%;
  --datatype-blue: 200 98% 39%;
  --datatype-red: 0 72.2% 50.6%;
  --datatype-violet: 262.1 83.3% 57.8%;
}
```

### Node Color Mapping System
**Category-based Node Colors:**
- **Input/Output**: Emerald (#10B981) / Red (#AA2411)
- **Models**: Fuchsia (#ab11ab)
- **Agents**: Purple (#903BBE)
- **Tools**: Cyan (#00fbfc)
- **Data**: Sky Blue (#198BF6)
- **Memory**: Amber (#F5B85A)

### Icon System Architecture
**Multi-source Icon Management:**
- **Lucide React**: Primary icon library with dynamic imports
- **FontAwesome**: Integration for brand icons
- **Custom Icons**: SVG components (GradientSave, BotMessageSquare)
- **Icon Caching**: Map-based caching system for performance
- **Lazy Loading**: Async icon loading with fallbacks

### Responsive Design Patterns
- **Mobile-first**: Tailwind breakpoints (sm: 640px, md: 768px, lg: 1024px, xl: 1200px)
- **Adaptive Layouts**: Grid/list view switching, collapsible sidebars
- **Touch Interactions**: Mobile-optimized button sizes and touch targets
- **Viewport Adaptation**: Responsive modal sizes, dynamic sidebar behavior
- **Progressive Disclosure**: Context-aware UI element visibility