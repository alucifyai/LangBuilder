# Frontend API Flow to Backend (localhost:3000 → localhost:7860)

## Software Stack

**Frontend Stack:**
- **Build Tool**: Vite 5.4.19 (modern build tool, replaces Create React App)
- **Framework**: React 18.3.1 with TypeScript 5.4.5
- **Dev Server**: Vite dev server on port 3000
- **HTTP Client**: Axios 1.7.4
- **State Management**: Zustand 4.5.2
- **UI Libraries**: Radix-UI, Tailwind CSS, Framer Motion
- **Styling**: Tailwind CSS with custom components

## API Connection Architecture

**1. Development Server Configuration (vite.config.mts:61-66)**
```typescript
server: {
  port: 3000,
  proxy: {
    "^/api/v1/": { target: "http://localhost:7860", changeOrigin: true, secure: false, ws: true },
    "^/api/v2/": { target: "http://localhost:7860", changeOrigin: true, secure: false, ws: true },
    "/health": { target: "http://localhost:7860", changeOrigin: true, secure: false, ws: true }
  }
}
```

**2. Proxy Configuration**
- Routes matching `/api/v1/`, `/api/v2/`, and `/health` are proxied to `http://localhost:7860`
- WebSocket support enabled (`ws: true`)
- CORS handled via `changeOrigin: true`

## Request Flow

**1. Frontend → Vite Dev Server (localhost:3000)**
- React app makes API calls using Axios
- Calls like `api.get('/api/v1/flows')` go to localhost:3000

**2. Vite Proxy → Backend (localhost:7860)**
- Vite dev server intercepts API routes and forwards to FastAPI backend
- No CORS issues due to proxy handling

**3. API Client Setup (api.tsx:22-24)**
```typescript
const api: AxiosInstance = axios.create({
  baseURL: baseURL, // Empty string in development
});
```

**4. Authentication & Interceptors**
- JWT token automatically added via request interceptors (api.tsx:152-187)
- Response interceptors handle 401/403 errors and token refresh
- Custom headers added for internal requests

**5. Backend Connection**
- Backend runs FastAPI on port 7860
- Database: SQLite in development (`src/backend/base/langflow/langflow.db`)
- API endpoints: `/api/v1/` and `/api/v2/`

## Key Configuration Files
- `vite.config.mts` - Dev server and proxy setup
- `src/frontend/src/customization/config-constants.ts` - API routes and proxy target
- `src/frontend/src/controllers/API/api.tsx` - Axios instance and interceptors
- `package.json` - Dependencies and scripts

This architecture allows seamless development with hot reloading while avoiding CORS issues through the Vite proxy layer.