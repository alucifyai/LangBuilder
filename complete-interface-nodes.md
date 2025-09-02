# Complete LangBuilder Interface Nodes

Based on deep analysis of the frontend codebase, here are all the interface components with their complete details, including UIDL definitions, state management, and layout elements.

**Last Updated:** Including Voice Mode, MCP support, and complete UI component library

## UIDL Structure Definitions

### Base UIDL Types
```typescript
interface UIDL {
  name: string
  type: 'page' | 'component' | 'store' | 'modal' | 'layout'
  content?: UIElement
  stateDefinitions?: StateDefinitions
  actions?: Actions
  props?: PropDefinitions
  events?: EventHandlers
}

interface UIElement {
  elementType: string  // 'container' | 'form' | 'button' | 'input' | etc.
  name?: string
  attrs?: Record<string, any>
  children?: UIElement[] | RepeatElement
  dependency?: string  // Reference to another component
  bindingPath?: string  // Data binding path
  conditional?: ConditionalRender
}

interface RepeatElement {
  repeat: {
    dataSource: string
    element: UIElement
    key?: string
  }
}

interface ConditionalRender {
  condition: string  // Expression to evaluate
  ifTrue?: UIElement
  ifFalse?: UIElement
}
```

## Main Application Pages with UIDL

### 1. LoginPage
**Route:** `/login`
**UIDL Definition:**
```typescript
{
  name: "LoginPage",
  type: "page",
  content: {
    elementType: "container",
    attrs: { className: "login-page" },
    children: [
      {
        elementType: "component",
        name: "Logo",
        dependency: "ui_logo_component"
      },
      {
        elementType: "form",
        name: "LoginForm",
        attrs: { onSubmit: "handleLogin" },
        children: [
          {
            elementType: "input",
            name: "UsernameInput",
            attrs: {
              type: "text",
              placeholder: "Username",
              required: true,
              bindingPath: "credentials.username"
            }
          },
          {
            elementType: "input",
            name: "PasswordInput",
            attrs: {
              type: "password",
              placeholder: "Password",
              required: true,
              bindingPath: "credentials.password"
            }
          },
          {
            elementType: "checkbox",
            name: "AutoLoginCheckbox",
            attrs: {
              label: "Keep me logged in",
              bindingPath: "autoLogin"
            }
          },
          {
            elementType: "button",
            name: "SubmitButton",
            attrs: {
              type: "submit",
              variant: "primary",
              loading: { bindingPath: "isLoading" }
            },
            children: [{ elementType: "text", content: "Sign In" }]
          }
        ]
      },
      {
        elementType: "link",
        attrs: { href: "/signup" },
        children: [{ elementType: "text", content: "Create Account" }]
      }
    ]
  },
  stateDefinitions: {
    credentials: {
      type: "object",
      defaultValue: { username: "", password: "" }
    },
    autoLogin: {
      type: "boolean",
      defaultValue: false
    },
    isLoading: {
      type: "boolean",
      defaultValue: false
    },
    error: {
      type: "string",
      defaultValue: null
    }
  },
  actions: {
    handleLogin: {
      type: "async",
      handler: "authService.login"
    }
  }
}
```

### 2. FlowDashboard (HomePage)
**Route:** `/flows`, `/components`, `/all`, `/mcp`
**UIDL Definition:**
```typescript
{
  name: "FlowDashboard",
  type: "page",
  content: {
    elementType: "container",
    attrs: { className: "dashboard-layout" },
    children: [
      {
        elementType: "component",
        name: "Header",
        dependency: "ui_dashboard_header"
      },
      {
        elementType: "container",
        name: "MainContent",
        attrs: { className: "dashboard-content" },
        children: [
          {
            elementType: "component",
            name: "FolderSidebar",
            dependency: "ui_folder_sidebar",
            conditional: {
              condition: "!isSmallScreen",
              ifFalse: null
            }
          },
          {
            elementType: "container",
            name: "ContentArea",
            children: [
              {
                elementType: "tabs",
                name: "DashboardTabs",
                attrs: {
                  activeTab: { bindingPath: "activeTab" }
                },
                children: [
                  {
                    elementType: "tab",
                    name: "FlowsTab",
                    attrs: { value: "flows", label: "Flows" },
                    children: [{
                      elementType: "component",
                      name: "FlowGrid",
                      dependency: "ui_flow_grid"
                    }]
                  },
                  {
                    elementType: "tab",
                    name: "ComponentsTab",
                    attrs: { value: "components", label: "Components" },
                    children: [{
                      elementType: "component",
                      name: "ComponentGrid",
                      dependency: "ui_component_grid"
                    }]
                  },
                  {
                    elementType: "tab",
                    name: "MCPTab",
                    attrs: { value: "mcp", label: "MCP Tools" },
                    children: [{
                      elementType: "component",
                      name: "MCPServerTab",
                      dependency: "ui_mcp_server_tab"
                    }]
                  }
                ]
              },
              {
                elementType: "component",
                name: "Paginator",
                dependency: "ui_paginator",
                conditional: {
                  condition: "totalItems > pageSize",
                  ifFalse: null
                }
              }
            ]
          }
        ]
      }
    ]
  },
  stateDefinitions: {
    activeTab: {
      type: "string",
      defaultValue: "flows"
    },
    flows: {
      type: "array",
      defaultValue: []
    },
    components: {
      type: "array",
      defaultValue: []
    },
    selectedFolder: {
      type: "string",
      defaultValue: null
    },
    searchQuery: {
      type: "string",
      defaultValue: ""
    },
    viewMode: {
      type: "string",
      defaultValue: "grid"  // 'grid' | 'list'
    },
    selectedItems: {
      type: "array",
      defaultValue: []
    },
    totalItems: {
      type: "number",
      defaultValue: 0
    },
    pageSize: {
      type: "number",
      defaultValue: 12
    },
    currentPage: {
      type: "number",
      defaultValue: 1
    }
  }
}
```

### 3. FlowEditor
**Route:** `/flow/:id`
**UIDL Definition:**
```typescript
{
  name: "FlowEditor",
  type: "page",
  content: {
    elementType: "container",
    attrs: { className: "flow-editor-layout" },
    children: [
      {
        elementType: "component",
        name: "FlowToolbar",
        dependency: "ui_flow_toolbar"
      },
      {
        elementType: "container",
        name: "EditorArea",
        attrs: { className: "editor-workspace" },
        children: [
          {
            elementType: "component",
            name: "ComponentSidebar",
            dependency: "ui_component_sidebar",
            attrs: {
              isOpen: { bindingPath: "sidebarOpen" }
            }
          },
          {
            elementType: "component",
            name: "ReactFlowCanvas",
            dependency: "ui_reactflow_wrapper",
            attrs: {
              nodes: { bindingPath: "nodes" },
              edges: { bindingPath: "edges" },
              onNodesChange: "handleNodesChange",
              onEdgesChange: "handleEdgesChange",
              onConnect: "handleConnect"
            }
          },
          {
            elementType: "component",
            name: "Minimap",
            dependency: "ui_minimap",
            conditional: {
              condition: "showMinimap",
              ifFalse: null
            }
          },
          {
            elementType: "component",
            name: "CanvasControls",
            dependency: "ui_canvas_controls"
          }
        ]
      }
    ]
  },
  stateDefinitions: {
    flowId: {
      type: "string",
      defaultValue: null
    },
    nodes: {
      type: "array",
      defaultValue: []
    },
    edges: {
      type: "array",
      defaultValue: []
    },
    selectedNode: {
      type: "object",
      defaultValue: null
    },
    sidebarOpen: {
      type: "boolean",
      defaultValue: true
    },
    showMinimap: {
      type: "boolean",
      defaultValue: false
    },
    executionState: {
      type: "string",
      defaultValue: "idle"  // 'idle' | 'building' | 'running' | 'success' | 'error'
    },
    buildStatus: {
      type: "object",
      defaultValue: {}
    },
    isDirty: {
      type: "boolean",
      defaultValue: false
    }
  }
}
```

### 4. PlaygroundInterface (Chat)
**Route:** `/playground/:id`
**UIDL Definition:**
```typescript
{
  name: "PlaygroundInterface",
  type: "page",
  content: {
    elementType: "container",
    attrs: { className: "playground-layout" },
    children: [
      {
        elementType: "component",
        name: "PlaygroundHeader",
        dependency: "ui_playground_header"
      },
      {
        elementType: "container",
        name: "PlaygroundContent",
        attrs: { className: "playground-content" },
        children: [
          {
            elementType: "component",
            name: "SessionSidebar",
            dependency: "ui_session_sidebar",
            conditional: {
              condition: "showSessions",
              ifFalse: null
            }
          },
          {
            elementType: "container",
            name: "ChatArea",
            children: [
              {
                elementType: "component",
                name: "MessageList",
                dependency: "ui_message_list",
                attrs: {
                  messages: { bindingPath: "messages" },
                  isStreaming: { bindingPath: "isStreaming" }
                }
              },
              {
                elementType: "component",
                name: "ChatInput",
                dependency: "ui_chat_input",
                attrs: {
                  onSend: "handleSendMessage",
                  voiceEnabled: { bindingPath: "voiceMode.enabled" }
                }
              },
              {
                elementType: "component",
                name: "VoiceAssistant",
                dependency: "ui_voice_assistant",
                conditional: {
                  condition: "voiceMode.enabled",
                  ifFalse: null
                }
              }
            ]
          }
        ]
      }
    ]
  },
  stateDefinitions: {
    sessionId: {
      type: "string",
      defaultValue: null
    },
    messages: {
      type: "array",
      defaultValue: []
    },
    sessions: {
      type: "array",
      defaultValue: []
    },
    showSessions: {
      type: "boolean",
      defaultValue: true
    },
    isStreaming: {
      type: "boolean",
      defaultValue: false
    },
    voiceMode: {
      type: "object",
      defaultValue: {
        enabled: false,
        isListening: false,
        selectedMicrophone: null,
        selectedVoice: null
      }
    },
    attachedFiles: {
      type: "array",
      defaultValue: []
    }
  }
}
```

## Modal Components with UIDL

### 1. IOModal (Playground Modal)
```typescript
{
  name: "IOModal",
  type: "modal",
  content: {
    elementType: "modal",
    attrs: {
      isOpen: { bindingPath: "isOpen" },
      onClose: "handleClose",
      size: "large"
    },
    children: [
      {
        elementType: "modalHeader",
        children: [
          { elementType: "text", content: "Playground" },
          {
            elementType: "button",
            attrs: { onClick: "toggleFullscreen" },
            children: [{ elementType: "icon", name: "maximize" }]
          }
        ]
      },
      {
        elementType: "modalBody",
        children: [
          {
            elementType: "tabs",
            children: [
              {
                elementType: "tab",
                attrs: { value: "chat", label: "Chat" },
                children: [{ elementType: "component", dependency: "ui_chat_view" }]
              },
              {
                elementType: "tab",
                attrs: { value: "inputs", label: "Inputs" },
                children: [{ elementType: "component", dependency: "ui_input_fields" }]
              },
              {
                elementType: "tab",
                attrs: { value: "outputs", label: "Outputs" },
                children: [{ elementType: "component", dependency: "ui_output_display" }]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 2. AddMCPServerModal
```typescript
{
  name: "AddMCPServerModal",
  type: "modal",
  content: {
    elementType: "modal",
    attrs: {
      isOpen: { bindingPath: "isOpen" },
      onClose: "handleClose"
    },
    children: [
      {
        elementType: "modalHeader",
        children: [{ elementType: "text", content: "Add MCP Server" }]
      },
      {
        elementType: "modalBody",
        children: [
          {
            elementType: "form",
            attrs: { onSubmit: "handleAddServer" },
            children: [
              {
                elementType: "input",
                attrs: {
                  label: "Server Name",
                  bindingPath: "serverName",
                  required: true
                }
              },
              {
                elementType: "select",
                attrs: {
                  label: "Server Type",
                  bindingPath: "serverType",
                  options: ["npx", "node", "python", "docker"]
                }
              },
              {
                elementType: "textarea",
                attrs: {
                  label: "Command",
                  bindingPath: "command",
                  placeholder: "npx @modelcontextprotocol/server-name"
                }
              },
              {
                elementType: "input",
                attrs: {
                  label: "Environment Variables",
                  bindingPath: "envVars",
                  type: "json"
                }
              }
            ]
          }
        ]
      },
      {
        elementType: "modalFooter",
        children: [
          {
            elementType: "button",
            attrs: { variant: "secondary", onClick: "handleClose" },
            children: [{ elementType: "text", content: "Cancel" }]
          },
          {
            elementType: "button",
            attrs: { variant: "primary", onClick: "handleAddServer" },
            children: [{ elementType: "text", content: "Add Server" }]
          }
        ]
      }
    ]
  }
}
```

## Reusable UI Components Library

### Core UI Components (src/components/ui/)
```typescript
// Base components following shadcn/ui patterns
- Accordion (accordion.tsx)
- Alert (alert.tsx)
- Badge (badge.tsx)
- Button (button.tsx)
- Card (card.tsx)
- Checkbox (checkbox.tsx)
- Command (command.tsx)
- Dialog (dialog.tsx)
- DropdownMenu (dropdown-menu.tsx)
- Input (input.tsx)
- Label (label.tsx)
- Popover (popover.tsx)
- Progress (progress.tsx)
- RadioGroup (radio-group.tsx)
- ScrollArea (scroll-area.tsx)
- Select (select.tsx)
- Separator (separator.tsx)
- Sheet (sheet.tsx)
- Skeleton (skeleton.tsx)
- Slider (slider.tsx)
- Switch (switch.tsx)
- Table (table.tsx)
- Tabs (tabs.tsx)
- Textarea (textarea.tsx)
- Toast (toast.tsx)
- Toggle (toggle.tsx)
- Tooltip (tooltip.tsx)
```

### Advanced Components
```typescript
// Background and Visual Effects
- BackgroundGradient (background-gradient.tsx)
- DotBackground (dot-background.tsx)
- BorderTrail (border-trail.tsx)

// Data Display
- DataTable (data-table.tsx)
- JsonViewer (json-viewer.tsx)
- CodeBlock (code-block.tsx)
- MarkdownRenderer (markdown-renderer.tsx)

// Form Components
- FormField (form-field.tsx)
- FormGroup (form-group.tsx)
- MultiSelect (multi-select.tsx)
- DatePicker (date-picker.tsx)
- TimePicker (time-picker.tsx)
- ColorPicker (color-picker.tsx)

// Loading States
- Loading (loading.tsx)
- LoadingText (loading-text.tsx)
- SkeletonCard (skeleton-card.tsx)
- Spinner (spinner.tsx)
```

### Voice Mode Components
```typescript
{
  name: "VoiceAssistant",
  type: "component",
  content: {
    elementType: "container",
    attrs: { className: "voice-assistant" },
    children: [
      {
        elementType: "component",
        name: "VoiceButton",
        dependency: "ui_voice_button",
        attrs: {
          isListening: { bindingPath: "isListening" },
          onClick: "toggleListening"
        }
      },
      {
        elementType: "component",
        name: "AudioWaveform",
        dependency: "ui_audio_waveform",
        conditional: {
          condition: "isListening",
          ifFalse: null
        }
      },
      {
        elementType: "component",
        name: "AudioSettings",
        dependency: "ui_audio_settings_dialog"
      }
    ]
  },
  stateDefinitions: {
    isListening: { type: "boolean", defaultValue: false },
    audioLevel: { type: "number", defaultValue: 0 },
    selectedMicrophone: { type: "string", defaultValue: null },
    selectedVoice: { type: "string", defaultValue: null },
    voiceProviders: {
      type: "array",
      defaultValue: ["OpenAI", "ElevenLabs"]
    }
  }
}
```

## State Management Architecture

### Zustand Store System with Types
```typescript
// authStore.ts
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  accessToken: string | null
  refreshToken: string | null
  autoLogin: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  refreshTokens: () => Promise<void>
  setUser: (user: User) => void
  checkAutoLogin: () => boolean
}

// flowStore.ts
interface FlowState {
  currentFlow: Flow | null
  nodes: Node[]
  edges: Edge[]
  isDirty: boolean
  executionState: 'idle' | 'building' | 'running' | 'success' | 'error'
  buildStatus: Record<string, BuildStatus>
  history: HistoryItem[]
  historyIndex: number
  loadFlow: (id: string) => Promise<void>
  saveFlow: () => Promise<void>
  addNode: (node: Node) => void
  removeNode: (nodeId: string) => void
  updateNode: (nodeId: string, data: Partial<NodeData>) => void
  addEdge: (edge: Edge) => void
  removeEdge: (edgeId: string) => void
  executeFlow: (inputs?: Record<string, any>) => Promise<void>
  undo: () => void
  redo: () => void
}

// messagesStore.ts
interface MessagesState {
  messages: Message[]
  sessions: Session[]
  currentSession: string | null
  isStreaming: boolean
  streamingMessage: Message | null
  addMessage: (message: Message) => void
  updateMessage: (id: string, update: Partial<Message>) => void
  deleteMessage: (id: string) => void
  loadMessages: (sessionId: string) => Promise<void>
  createSession: () => string
  switchSession: (sessionId: string) => void
  clearSession: (sessionId: string) => void
}

// voiceStore.ts
interface VoiceState {
  isEnabled: boolean
  isListening: boolean
  isSpeaking: boolean
  selectedMicrophone: string | null
  selectedVoice: string | null
  voiceProvider: 'openai' | 'elevenlabs'
  audioLevel: number
  transcript: string
  setListening: (listening: boolean) => void
  setSpeaking: (speaking: boolean) => void
  setMicrophone: (deviceId: string) => void
  setVoice: (voiceId: string) => void
  setProvider: (provider: string) => void
  updateAudioLevel: (level: number) => void
  appendTranscript: (text: string) => void
  clearTranscript: () => void
}

// mcpStore.ts (New)
interface MCPState {
  servers: MCPServer[]
  tools: MCPTool[]
  activeServer: string | null
  loadServers: () => Promise<void>
  addServer: (server: MCPServer) => Promise<void>
  removeServer: (serverId: string) => Promise<void>
  activateServer: (serverId: string) => void
  loadTools: (serverId: string) => Promise<void>
  executeTool: (toolId: string, params: any) => Promise<any>
}
```

## Layout Elements and Patterns

### Grid System
```typescript
{
  elementType: "grid",
  attrs: {
    columns: { sm: 1, md: 2, lg: 3, xl: 4 },
    gap: "medium",
    responsive: true
  },
  children: {
    repeat: {
      dataSource: "items",
      element: {
        elementType: "component",
        dependency: "ui_grid_item"
      }
    }
  }
}
```

### Flex Layout
```typescript
{
  elementType: "flex",
  attrs: {
    direction: "row", // 'row' | 'column'
    justify: "space-between", // 'start' | 'end' | 'center' | 'space-between' | 'space-around'
    align: "center", // 'start' | 'end' | 'center' | 'stretch'
    wrap: true,
    gap: "small"
  }
}
```

### Split Pane
```typescript
{
  elementType: "splitPane",
  attrs: {
    orientation: "horizontal", // 'horizontal' | 'vertical'
    defaultSize: 300,
    minSize: 200,
    maxSize: 500,
    resizable: true
  },
  children: [
    { elementType: "component", dependency: "ui_left_pane" },
    { elementType: "component", dependency: "ui_right_pane" }
  ]
}
```

## Screen State Transitions

### Flow Editor States
```typescript
stateMachine: {
  initial: "loading",
  states: {
    loading: {
      on: {
        LOAD_SUCCESS: "idle",
        LOAD_ERROR: "error"
      }
    },
    idle: {
      on: {
        START_BUILD: "building",
        START_RUN: "validating",
        EDIT_NODE: "editing"
      }
    },
    editing: {
      on: {
        SAVE: "saving",
        CANCEL: "idle"
      }
    },
    saving: {
      on: {
        SAVE_SUCCESS: "idle",
        SAVE_ERROR: "error"
      }
    },
    building: {
      on: {
        BUILD_SUCCESS: "ready",
        BUILD_ERROR: "error"
      }
    },
    validating: {
      on: {
        VALIDATION_SUCCESS: "running",
        VALIDATION_ERROR: "error"
      }
    },
    running: {
      on: {
        RUN_SUCCESS: "completed",
        RUN_ERROR: "error",
        CANCEL: "idle"
      }
    },
    completed: {
      on: {
        RESET: "idle",
        RUN_AGAIN: "running"
      }
    },
    error: {
      on: {
        RETRY: "idle",
        DISMISS: "idle"
      }
    }
  }
}
```

### Authentication Flow States
```typescript
stateMachine: {
  initial: "checking",
  states: {
    checking: {
      on: {
        HAS_TOKEN: "validating",
        NO_TOKEN: "unauthenticated"
      }
    },
    validating: {
      on: {
        VALID_TOKEN: "authenticated",
        INVALID_TOKEN: "unauthenticated"
      }
    },
    unauthenticated: {
      on: {
        LOGIN: "authenticating",
        SIGNUP: "registering"
      }
    },
    authenticating: {
      on: {
        SUCCESS: "authenticated",
        ERROR: "unauthenticated",
        MFA_REQUIRED: "mfa_challenge"
      }
    },
    mfa_challenge: {
      on: {
        MFA_SUCCESS: "authenticated",
        MFA_ERROR: "unauthenticated"
      }
    },
    authenticated: {
      on: {
        LOGOUT: "unauthenticated",
        TOKEN_EXPIRED: "refreshing"
      }
    },
    refreshing: {
      on: {
        REFRESH_SUCCESS: "authenticated",
        REFRESH_ERROR: "unauthenticated"
      }
    }
  }
}
```

## Navigation Patterns

### Protected Routes with Guards
```typescript
// Route definitions with guards
const routes = [
  {
    path: "/",
    element: <AppWrapper />,
    children: [
      {
        path: "login",
        element: <ProtectedLoginRoute><LoginPage /></ProtectedLoginRoute>
      },
      {
        path: "flows",
        element: <ProtectedRoute><FlowDashboard /></ProtectedRoute>
      },
      {
        path: "flow/:id",
        element: <ProtectedRoute><FlowEditor /></ProtectedRoute>
      },
      {
        path: "admin",
        element: <ProtectedAdminRoute><AdminPage /></ProtectedAdminRoute>
      },
      {
        path: "settings",
        element: <AuthSettingsGuard><SettingsPage /></AuthSettingsGuard>,
        children: [
          { path: "general", element: <GeneralSettings /> },
          { path: "api-keys", element: <ApiKeysSettings /> },
          { path: "global-variables", element: <GlobalVariablesSettings /> },
          { path: "mcp-servers", element: <MCPServersSettings /> }
        ]
      }
    ]
  }
]
```

## Feature Flags and Conditional Features
```typescript
const FEATURE_FLAGS = {
  ENABLE_CUSTOM_PARAM: process.env.REACT_APP_ENABLE_CUSTOM_PARAM === 'true',
  ENABLE_FILE_MANAGEMENT: process.env.REACT_APP_ENABLE_FILE_MANAGEMENT === 'true',
  ENABLE_MCP: process.env.REACT_APP_ENABLE_MCP === 'true',
  ENABLE_VOICE_MODE: process.env.REACT_APP_ENABLE_VOICE_MODE === 'true',
  ENABLE_DATASTAX_LANGFLOW: process.env.REACT_APP_ENABLE_DATASTAX_LANGFLOW === 'true',
  ENABLE_WORKSPACE: process.env.REACT_APP_ENABLE_WORKSPACE === 'true'
}

// Conditional rendering based on feature flags
{
  conditional: {
    condition: "FEATURE_FLAGS.ENABLE_MCP",
    ifTrue: {
      elementType: "component",
      dependency: "ui_mcp_features"
    },
    ifFalse: null
  }
}
```

## Error Boundaries and Loading States
```typescript
{
  name: "ErrorBoundary",
  type: "component",
  content: {
    elementType: "errorBoundary",
    attrs: {
      fallback: {
        elementType: "component",
        dependency: "ui_error_fallback"
      }
    },
    children: [
      {
        elementType: "suspense",
        attrs: {
          fallback: {
            elementType: "component",
            dependency: "ui_loading_spinner"
          }
        },
        children: [
          {
            elementType: "component",
            dependency: "ui_main_content"
          }
        ]
      }
    ]
  }
}
```

## Accessibility Features
```typescript
{
  elementType: "button",
  attrs: {
    "aria-label": "Save flow",
    "aria-pressed": { bindingPath: "isSaving" },
    "aria-disabled": { bindingPath: "isDisabled" },
    role: "button",
    tabIndex: 0,
    onKeyDown: "handleKeyPress"
  }
}
```

## Responsive Design Breakpoints
```typescript
const breakpoints = {
  xs: '0px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px'
}

// Responsive attributes in UIDL
{
  attrs: {
    className: {
      xs: "col-span-12",
      md: "col-span-6",
      lg: "col-span-4"
    },
    display: {
      xs: "block",
      lg: "flex"
    }
  }
}
```

## Theme System
```typescript
interface ThemeDefinition {
  colors: {
    primary: string
    secondary: string
    background: string
    foreground: string
    muted: string
    accent: string
    destructive: string
    border: string
    input: string
    ring: string
  }
  spacing: {
    xs: string
    sm: string
    md: string
    lg: string
    xl: string
  }
  borderRadius: {
    sm: string
    md: string
    lg: string
    full: string
  }
  fontFamily: {
    sans: string
    mono: string
  }
}
```

## Summary

This complete interface documentation covers:
1. **UIDL Definitions**: Structured representation of all UI components
2. **Pages**: All main application screens with complete state management
3. **Modals**: Including new MCP and Voice Mode modals
4. **Components**: Full UI component library based on shadcn/ui
5. **State Management**: Complete Zustand store definitions with types
6. **Layout Systems**: Grid, Flex, and Split Pane patterns
7. **State Machines**: Flow editor and authentication state transitions
8. **Navigation**: Protected routes and guards
9. **Feature Flags**: Conditional feature enabling
10. **Accessibility**: ARIA attributes and keyboard navigation
11. **Responsive Design**: Breakpoint system
12. **Theme System**: Complete theming architecture

The UIDL approach provides a declarative, type-safe way to define UI components that can be:
- Validated at build time
- Transformed into different frameworks
- Used for code generation
- Analyzed for dependencies
- Optimized for performance