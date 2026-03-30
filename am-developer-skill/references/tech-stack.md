# Tech Stack — Recommended Libraries & Frameworks

Opinionated recommendations. Chọn dựa trên: ecosystem maturity, DX, performance, community support.

> **Nguyên tắc:** Prefer battle-tested > bleeding-edge. Fewer dependencies > more. Full-stack solution > glue nhiều lib.

## Frontend

| Nhu cầu | Recommend | Alternatives | Tránh |
|---------|-----------|-------------|-------|
| Web app (full-stack) | **Next.js 15** (App Router + API Routes) — default choice, 1 app = frontend + API. Chỉ tách backend riêng khi user yêu cầu hoặc cần scale độc lập | Nuxt 4 (Vue), Remix | CRA (deprecated) |
| SPA thuần | **Vite + React** | Vite + Vue, Svelte | Webpack manual setup |
| Mobile | **React Native + Expo** | Flutter | Cordova, Ionic |
| Desktop | **Electron** (nhanh) / **Tauri** (nhẹ) | — | — |
| Landing page (dynamic/SaaS) | **Next.js + Framer Motion** | — | WordPress |
| Landing page (static/brochure) | **Astro + Tailwind** hoặc **Next.js (export static)** | — | — |

### UI & Styling

| Nhu cầu | Recommend | Alternatives |
|---------|-----------|-------------|
| Component library | **shadcn/ui** (copy-paste, customizable) — bắt buộc cho admin/dashboard | Radix UI (headless) |
| CSS framework | **Tailwind CSS** — luôn dùng, không dùng CSS Modules hay Styled Components | — |
| Animation | **Framer Motion** | GSAP (complex), CSS transitions (simple) |
| Icons | **Lucide React** | Heroicons, Phosphor |
| Charts | **Recharts** | Chart.js, D3 (complex) |
| Forms | **React Hook Form + Zod** | Formik (heavier) |
| State management | **Zustand** (simple) / **TanStack Query** (server state) | Jotai, Redux Toolkit |
| Tables | **TanStack Table** | AG Grid (enterprise) |
| Date picker | **date-fns + react-day-picker** | dayjs, Luxon |
| Rich text editor | **Tiptap** | Slate, Quill |
| File upload | **Filepond** / **react-dropzone** | — |
| Toast/notification | **Sonner** | react-hot-toast |

## Backend

| Nhu cầu | Recommend | Alternatives | Tránh |
|---------|-----------|-------------|-------|
| API server (tách riêng) | **NestJS** (structured, DI, modular) — chỉ khi cần tách backend: microservices, scale độc lập, team riêng, hoặc user yêu cầu | Fastify, Express | Koa (ít maintain) |
| Lightweight API / Edge | **Hono** (fast, CF Workers compatible) | Express (mature) | — |
| API (Python) | **FastAPI** | Django REST, Flask | — |
| API (Go) | **Gin** / **Echo** | Chi, Fiber | — |
| Realtime / WebSocket | **Socket.io** | ws (lightweight), Hono WebSocket | — |
| Background jobs | **BullMQ** (Redis-based) | Agenda (MongoDB) | — |
| Cron/scheduling | **node-cron** | croner | — |
| Email | **Resend** | Nodemailer + SES, Postmark | SendGrid (pricing) |

### API Design

| Nhu cầu | Recommend | Khi nào |
|---------|-----------|---------|
| REST API (trong Next.js) | **Next.js API Routes** (default) | Khi chưa cần tách backend |
| REST API (tách riêng) | **NestJS** / **Hono** (edge) | Microservices, scale độc lập, team riêng |
| Type-safe API | **tRPC** | Fullstack TypeScript, internal APIs |
| GraphQL | **Apollo Server** / **Yoga** | Complex data graph, mobile apps multi-query |
| Realtime | **WebSocket + Socket.io** | Chat, live updates, notifications |

## Database

| Nhu cầu | Recommend | Alternatives | Khi nào |
|---------|-----------|-------------|---------|
| Relational (chính) | **PostgreSQL** | MySQL | Hầu hết projects |
| ORM (TypeScript) | **Drizzle ORM** | Prisma (heavier), Kysely (query builder) | Type-safe DB access |
| NoSQL / Document | **MongoDB** | — | Schema linh hoạt, prototyping |
| KV / Cache | **Redis** | Memcached | Caching, sessions, queues |
| SQLite (embedded) | **better-sqlite3** / **Turso** | D1 (Cloudflare) | Edge, mobile, small apps |
| Vector DB | **Pinecone** / **pgvector** | Weaviate, Qdrant | AI/embeddings |
| Search | **Meilisearch** | Typesense, Elasticsearch (heavy) | Full-text search |

### Database Guidelines

- **Default PostgreSQL** — trừ khi có lý do cụ thể dùng cái khác
- **Drizzle > Prisma** cho projects mới — nhẹ hơn, SQL-like, không cần generate client
- **Luôn có migration** — không modify schema bằng tay
- **Connection pooling** — dùng pgBouncer hoặc built-in pool cho production
- **User không có DB / không setup được** → dùng managed free tier: **Supabase** (PostgreSQL, 500MB free), **Neon** (serverless PG, free tier), **Turso** (SQLite edge, 9GB free)

## Auth & Security

| Nhu cầu | Recommend | Alternatives |
|---------|-----------|-------------|
| Auth (Project stack) | **auth-cloud-flare-workspace** — multi-tenant OAuth 2.0 + OIDC, Cloudflare Workers + D1 + KV | — |
| Auth (managed) | **Clerk** | Auth0, Supabase Auth |
| Auth (self-hosted, other) | **Auth.js v5** / **Better Auth** | Passport.js (legacy) |
| JWT | **jose** (Edge-compatible) | jsonwebtoken |
| Password hashing | **bcrypt** / **argon2** | — |
| Rate limiting | **rate-limiter-flexible** | express-rate-limit |
| Input validation | **Zod** | Joi, Yup |
| CORS | Built-in framework support | cors package |

### Auth Integration — Identity Server

Reference repo: [your-org/auth-cloud-flare-workspace](https://github.com/your-org/auth-cloud-flare-workspace)

**Stack:** Hono + jose + Zod + Cloudflare D1 + KV

**Khi nào dùng:** Project cần auth cho web + mobile, self-hosted trên Cloudflare, multi-tenant SaaS.
**Khi nào KHÔNG dùng:** Prototype nhanh → Clerk/Supabase Auth. Single app đơn giản → Auth.js v5.

**Mỗi user/team tạo tenant riêng và tự quản lý** — không cần admin access. Tenant có: credentials, redirect URIs, allowed apps.

#### Tích hợp Web App (Hono / Next.js)

**1. Env vars cần thiết:**
```env
IDENTITY_SERVER_URL=https://auth.example.com
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
WEB_CLIENT_URL=https://yourapp.com
```

**2. OAuth flow (Authorization Code + PKCE):**
```
User click Login → POST /login (generate PKCE, store verifier in httpOnly cookie)
  → Redirect to identity-server /oauth/authorize
  → User authenticates (Google/Apple/Facebook)
  → Redirect back to /callback with code
  → Exchange code + PKCE verifier for tokens
  → Store access_token + refresh_token in httpOnly cookies
  → Redirect to dashboard
```

**3. Identity Client (core service):**
```typescript
class IdentityClient {
  constructor(env: { IDENTITY_SERVER_URL, CLIENT_ID, CLIENT_SECRET }) { ... }

  // Build OAuth authorize URL (với PKCE + state)
  buildAuthorizeUrl(params: { provider, codeChallenge, state, scope? }): string

  // Exchange authorization code for tokens
  exchangeCode(params: { code, codeVerifier }): Promise<TokenResponse>

  // Refresh access token
  refreshToken(refreshToken: string): Promise<TokenResponse>

  // Revoke token on logout
  revokeToken(token: string): Promise<void>

  // Get user info
  getUserInfo(accessToken: string): Promise<UserInfo>
}
```

**4. Auth middleware (protect routes):**
```typescript
// Validate JWT locally using JWKS (RS256) — no introspection needed (<5ms)
// Proactive refresh: nếu token < 5 phút trước khi hết hạn → auto refresh
// Invalid/expired → redirect /login

authMiddleware() → validates access_token cookie → sets c.user → next()
```

**5. Token storage (httpOnly cookies):**
```
access_token:  httpOnly, Secure, SameSite=Lax,    maxAge=1h
refresh_token: httpOnly, Secure, SameSite=Strict,  maxAge=7d
pkce_verifier: httpOnly, Secure, SameSite=Lax,    maxAge=10min (temp)
```

**6. Routes cần implement:**
```
POST /login     → initiate OAuth (generate PKCE, redirect to identity-server)
GET  /callback  → handle callback (exchange code, set cookies)
POST /logout    → revoke token, clear cookies
```

#### Tích hợp Mobile App (React Native + Expo)

**1. Dependencies:**
```bash
npx expo install expo-web-browser expo-secure-store expo-apple-authentication
npm install @react-native-google-signin/google-signin
```

**2. Env vars:**
```env
EXPO_PUBLIC_CLIENT_ID=mobile-client
EXPO_PUBLIC_IDENTITY_SERVER_URL=https://auth.example.com
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=xxx.apps.googleusercontent.com
```

**3. OAuth flow (platform-specific best UX):**
```
iOS:
  - Apple → Native Apple Sign-In (Face ID/Touch ID) → exchange identity token
  - Google → Web-based OAuth (expo-web-browser) → PKCE flow

Android:
  - Google → Native Google Sign-In (one-tap) → exchange ID token
  - Apple → Web-based OAuth (expo-web-browser) → PKCE flow
```

**4. Token storage:** `expo-secure-store` (Keychain on iOS, EncryptedSharedPreferences on Android)

**5. Auth hook (wrap entire app):**
```tsx
// AuthProvider wraps app, provides:
const { isAuthenticated, isLoading, user, login, logout, getAccessToken } = useAuth();

// Login
await login('google');  // or 'apple'

// Get valid token (auto-refresh if near expiry)
const token = await getAccessToken();

// Logout
await logout();
```

**6. Auto refresh:** Token tự refresh khi < 5 phút trước expiry via `getValidAccessToken()`.

#### API Endpoints (Identity Server)

```
OAuth:
  GET  /oauth/authorize          → Initiate auth flow
  POST /oauth/token              → Exchange code/refresh for tokens
  POST /oauth/revoke             → Revoke token
  GET  /oauth/userinfo           → Get user claims
  GET  /.well-known/openid-configuration
  GET  /.well-known/jwks.json

Tenant self-service (Basic Auth với client_id:client_secret):
  GET/PATCH /api/v1/tenant                    → Tenant info
  GET/POST  /api/v1/tenant/credentials        → Manage credentials
  POST      /api/v1/tenant/credentials/:id/rotate
  GET/POST  /api/v1/tenant/redirect-uris      → Manage redirect URIs
  GET/POST  /api/v1/tenant/allowed-apps       → Manage allowed apps

Swagger UI: /docs
```

## Hosting & Deploy

| Nhu cầu | Recommend | Alternatives |
|---------|-----------|-------------|
| Frontend (static/SSR) | **Vercel** / **Cloudflare Pages** | Netlify |
| Backend API | **Railway** / **Fly.io** | Render, DigitalOcean App Platform |
| Edge functions | **Cloudflare Workers** | Vercel Edge, Deno Deploy |
| Docker / VPS | **Docker Compose** | Kubernetes (khi cần scale) |
| Database hosting | **Supabase** (PG) / **Neon** (serverless PG) | Railway, Turso |
| File storage | **Cloudflare R2** (S3-compatible, no egress fee) | AWS S3, Backblaze B2 |
| CDN | **Cloudflare** | CloudFront, Fastly |
| DNS | **Cloudflare** | Route53 |
| Monitoring | **Sentry** (errors) / **Axiom** (logs) | Datadog (expensive) |

## Testing

| Nhu cầu | Recommend | Alternatives |
|---------|-----------|-------------|
| Unit test | **Vitest** | Jest |
| E2E test | **Playwright** | Cypress |
| API test | **Vitest + supertest** | Postman/Newman |
| Component test | **Testing Library** | Enzyme (deprecated) |

## AI / LLM

| Nhu cầu | Recommend | Alternatives |
|---------|-----------|-------------|
| LLM API client | **Vercel AI SDK** | LangChain (heavy), direct API |
| Embeddings | **OpenAI text-embedding-3-small** | Cohere, local models |
| Vector search | **pgvector** (nếu đã dùng PG) | Pinecone (managed) |
| Structured output | **Zod + AI SDK** | instructor-js |

## Recommended Stacks (theo use case)

### By Project Type

| Use case | Stack |
|----------|-------|
| **SaaS MVP** | Next.js (full-stack: SSR + API Routes) + Drizzle + PostgreSQL + Vercel. Auth: Clerk (nhanh) hoặc custom auth (self-hosted). Tách NestJS chỉ khi cần |
| **E-commerce** | Next.js + Medusa.js (headless) hoặc Shopify Storefront API + NestJS |
| **Brochure/Giới thiệu** (nhà hàng, salon, portfolio...) | Astro + Tailwind + Cloudflare Pages — static, fast, free hosting |
| **Blog/Content** | Astro + MDX + Cloudflare Pages |
| **Internal tool/Admin** | Next.js + shadcn/ui + Tailwind + Drizzle + PostgreSQL |
| **Chat/Realtime** | Next.js + NestJS + Socket.io + Redis + BullMQ |
| **CLI tool** | Commander.js + Inquirer + chalk |
| **Chrome extension** | Plasmo + React |
| **API-only** | NestJS + Drizzle + PostgreSQL + Railway |
| **AI chatbot/agent** | Vercel AI SDK + OpenAI + NestJS + pgvector + Redis |
| **Mobile app** | Expo + React Native + NestJS (API) + Supabase |

### By Budget

| Constraint | Stack |
|-----------|-------|
| **Zero budget** | Cloudflare Workers (Hono) + D1 + R2 + Pages — all free tier |
| **Low budget** | Next.js (Vercel free) + NestJS (Railway free) + Supabase (free PG) |
| **Prototype/Hackathon** | Next.js + Supabase (DB + Auth + Storage all-in-one) |
| **Production** | NestJS + PostgreSQL + Redis + BullMQ + Sentry + Cloudflare |

### By Deployment

| Constraint | Stack |
|-----------|-------|
| **Edge-first** | Hono + Cloudflare Workers + D1/Turso + KV |
| **Self-hosted** | Docker Compose + Caddy + NestJS + PostgreSQL + MinIO |
| **Serverless** | Next.js (Vercel) + Hono (CF Workers) + Neon (serverless PG) |

### Chọn nhanh

```
User hỏi build app/web?
  ├─ Static/brochure (nhà hàng, portfolio...)? → Astro + Cloudflare Pages
  ├─ Web app (default)? → Next.js full-stack (SSR + API Routes) — 1 app, 1 deploy
  │   ├─ User yêu cầu tách backend? → + NestJS
  │   └─ Cần microservices/scale? → + NestJS
  ├─ SPA thuần (no SSR)? → Vite + React
  ├─ User muốn tiết kiệm? → Cloudflare stack (Workers + D1 + R2 + Pages)
  ├─ User không có DB? → Supabase / Neon free tier
  └─ Mobile? → Expo + React Native + Next.js API (hoặc NestJS nếu tách)
```

## Quy tắc chọn stack

1. **Project đã có stack → dùng stack đó.** Không migrate mid-project trừ khi có lý do critical.
2. **Project mới → hỏi user preference trước.** Nếu user không có preference → dùng recommendations trên.
3. **Repo mặc định GitHub.** Tên repo: `<project-name>-workspace` (ví dụ: `restaurant-workspace`, `saas-workspace`).
4. **Monorepo → Turborepo.** Multi-package → pnpm workspaces.
5. **Typescript mọi nơi.** Trừ khi project yêu cầu ngôn ngữ khác.
6. **Fewer dependencies > more.** Mỗi dependency là tech debt. Chỉ thêm khi tự viết mất > 2h.
7. **Check npm weekly downloads + last publish date** trước khi recommend lib mới. Dead lib = risk.
