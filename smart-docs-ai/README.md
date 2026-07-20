# Smart Docs AI — Frontend
Đồ án thực tập AWS — Ứng dụng hỏi đáp tài liệu thông minh sử dụng RAG (Retrieval-Augmented Generation) chạy trên AWS.

---

## Hướng dẫn cài đặt và chạy dự án

1. Mở **Terminal** tại thư mục muốn lưu dự án, clone repo:
```shell
git clone https://github.com/TakunKenjo/SmartdocAI-AWS.git
```

2. Truy cập vào thư mục frontend:
```shell
cd smart-docs-ai\smart-docs-ai
```

3. Cài đặt các dependencies (yêu cầu Node.js đã được cài đặt):
```shell
npm install
```

4. Copy file môi trường mẫu và đặt tên thành `.env`:
```shell
copy .env-example .env
```
Điền giá trị `VITE_API_BASE_URL` vào file `.env` (URL của API Gateway trên AWS).

5. Khởi động dự án:
```shell
npm run dev
```

6. Truy cập vào `http://localhost:5173/` để sử dụng.

> **Lưu ý:** Lệnh `npm run dev:all` sẽ chạy thêm cả `json-server` (mock API cục bộ trên port 3001) song song với Vite — dùng trong quá trình phát triển khi chưa có backend thực.

---

## 1. STACK CÔNG NGHỆ

| Thành phần | Công nghệ |
|---|---|
| Framework UI | React 19 |
| Build Tool | Vite 7 |
| Routing | React Router v7 |
| State Management | Redux Toolkit v2 |
| Styling | Tailwind CSS v4 |
| Component Library | Shadcn/ui (Radix UI) |
| HTTP Client | Axios |
| Xác thực | AWS Cognito (`amazon-cognito-identity-js`) |
| Icons | Lucide React, FontAwesome |
| Font | Geist Variable (`@fontsource-variable/geist`) |
| Notifications | Sonner (toast) |
| Charts | Chart.js + react-chartjs-2 |
| Mock API (dev) | json-server |

---

## 2. GIẢI THÍCH CẤU TRÚC THƯ MỤC DỰ ÁN

### 2.1. Cấu trúc tổng quan

```
smart-docs-ai/                         # Thư mục gốc của frontend
├── public/                            # Tài nguyên tĩnh (favicon, logo...)
│
├── src/
│   ├── api/                           # Cấu hình HTTP & tích hợp AWS
│   │   ├── axiosConfig.js             # Axios instance + interceptor (tự gắn Bearer token, retry 503/504)
│   │   ├── cognito.js                 # Kết nối AWS Cognito UserPool, helper lấy JWT token
│   │   └── services/
│   │       ├── smartdocService.js     # Các API call: upload, process, chat, files, history...
│   │       └── profileService.js     # Các API call: getProfile, updatePersonalInfo, updateAvatar, changePassword
│   │
│   ├── assets/                        # Tài nguyên tĩnh (hình ảnh, icon...)
│   │
│   ├── components/                    # Shared/reusable components
│   │   ├── common/                    # Components tiện ích dùng chung
│   │   │   ├── Loading.jsx            # Spinner loading
│   │   │   ├── LoadMore.jsx           # Nút tải thêm
│   │   │   └── alert/
│   │   │       └── FailedAlert.jsx    # Alert báo lỗi
│   │   │
│   │   └── ui/                        # Shadcn/ui components (Radix-based)
│   │       ├── alert.jsx
│   │       ├── badge.jsx
│   │       ├── button.jsx
│   │       ├── card.jsx
│   │       ├── dialog.jsx
│   │       ├── dropdown-menu.jsx
│   │       ├── input.jsx
│   │       ├── label.jsx
│   │       ├── progress.jsx
│   │       ├── radio-group.jsx
│   │       ├── select.jsx
│   │       ├── sonner.jsx             # Toaster provider (Sonner)
│   │       ├── spinner.jsx
│   │       ├── switch.jsx
│   │       ├── tabs.jsx
│   │       └── toggle.jsx
│   │
│   ├── contexts/                      # React Context API
│   │   └── ThemeContext.jsx           # Quản lý Dark/Light mode (lưu vào localStorage)
│   │
│   ├── features/                      # Modules theo tính năng (Feature-Sliced Design)
│   │   ├── auth/                      # Xác thực người dùng
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.jsx      # Form đăng nhập (gọi Cognito qua Redux thunk)
│   │   │   │   ├── RegisterForm.jsx   # Form đăng ký (gọi backend API)
│   │   │   │   └── ProtectedRoute.jsx # HOC bảo vệ route (kiểm tra isAuthenticated)
│   │   │   └── pages/
│   │   │       ├── LoginPage.jsx      # Trang đăng nhập
│   │   │       └── RegisterPage.jsx   # Trang đăng ký
│   │   │
│   │   ├── profile/                   # Hồ sơ cá nhân
│   │   │   ├── components/
│   │   │   │   ├── ProfileAvatar.jsx  # Upload & hiển thị avatar
│   │   │   │   ├── PersonalInfoTab.jsx# Tab chỉnh sửa thông tin cá nhân
│   │   │   │   └── SecurityTab.jsx    # Tab đổi mật khẩu
│   │   │   └── pages/
│   │   │       └── ProfilePage.jsx    # Trang hồ sơ (tabs: Thông tin / Bảo mật)
│   │   │
│   │   └── smartdocs/                 # Tính năng chính: RAG Chat với tài liệu
│   │       ├── components/
│   │       │   ├── chat/              # Khu vực hội thoại
│   │       │   │   ├── ChatArea.jsx           # Container chính của chat (layout trái/phải)
│   │       │   │   ├── ChatInput.jsx          # Ô nhập câu hỏi + nút gửi
│   │       │   │   ├── ChatMessage.jsx        # Hiển thị 1 tin nhắn (user / AI)
│   │       │   │   ├── WelcomeHero.jsx        # Màn hình chào khi chưa có chat
│   │       │   │   ├── SearchSettings.jsx     # Cài đặt RAG (SelfRAG, CoRAG, top_k...)
│   │       │   │   ├── CoRagMetadata.jsx      # Hiển thị metadata CoRAG
│   │       │   │   ├── SelfRagMetadata.jsx    # Hiển thị metadata SelfRAG
│   │       │   │   └── SourceCitationPanel.jsx# Bảng nguồn trích dẫn của câu trả lời
│   │       │   │
│   │       │   ├── layout/            # Layout tổng thể của trang SmartDoc
│   │       │   │   └── SmartSidebar.jsx       # Sidebar chính (collapsible, responsive mobile)
│   │       │   │
│   │       │   └── sidebar/           # Các sub-component bên trong Sidebar
│   │       │       ├── StatusBadge.jsx        # Badge trạng thái kết nối LLM
│   │       │       ├── KpiRow.jsx             # Hàng thống kê (số file, trang, chunk)
│   │       │       ├── ChunkSettings.jsx      # Cài đặt chunk_size / chunk_overlap
│   │       │       ├── FileUploader.jsx        # Khu vực drag-and-drop upload tài liệu
│   │       │       ├── FileCard.jsx           # Card hiển thị 1 file đã xử lý
│   │       │       ├── FileList.jsx           # Danh sách các file đã xử lý
│   │       │       ├── ActionButtons.jsx      # Nút xoá tài liệu / xoá lịch sử chat
│   │       │       └── ChatHistoryList.jsx    # Danh sách lịch sử hội thoại
│   │       │
│   │       └── pages/
│   │           └── SmartdocPage.jsx   # Entry page: ghép SmartSidebar + ChatArea
│   │
│   ├── lib/                           # Utility functions & helpers
│   │   ├── utils.js                   # classNames utility (cn — kết hợp clsx + tailwind-merge)
│   │   ├── helpers.js                 # Các hàm tiện ích: formatDate, buildCategoryById, calculatePercent...
│   │   ├── alertUtils.js              # Tiện ích hiển thị thông báo (toast / alert)
│   │   └── goalUtils.js              # Tiện ích tính toán mục tiêu
│   │
│   ├── store/                         # Redux Toolkit store
│   │   ├── index.js                   # Cấu hình store (combineReducers: auth + smartdoc)
│   │   ├── README.md                  # Giải thích kỹ thuật createSelector / memoization
│   │   └── slices/
│   │       ├── authSlice.js           # State xác thực: login, register, logout, getProfile, thông tin user
│   │       └── smartdocSlice.js       # State SmartDoc: files, chat history, Ollama status, messages
│   │
│   ├── App.jsx                        # Root component: định nghĩa Routes, ThemeProvider, Toaster
│   ├── main.jsx                       # Entry point: mount React vào DOM, bọc BrowserRouter + Redux Provider
│   └── index.css                      # Global styles + Tailwind directives
│
├── .env-example                       # Template biến môi trường
├── buildspec.yml                      # AWS CodeBuild config (CI/CD)
├── components.json                    # Cấu hình Shadcn/ui
├── eslint.config.js                   # ESLint config
├── index.html                         # HTML entry point (Vite)
├── jsconfig.json                      # Path alias config cho IDE
├── package.json
├── tailwind.config.js                 # Tailwind CSS config
├── vite.config.js                     # Vite config (proxy API → AWS API Gateway, path alias @/)
└── README.md
```

---

### 2.2. Giải thích chi tiết từng thư mục

#### `src/api/`
Tầng giao tiếp với backend AWS.

- **`axiosConfig.js`**: Tạo một `axiosClient` dùng chung với `baseURL` lấy từ biến môi trường `VITE_API_BASE_URL`. Có 2 interceptor quan trọng:
  - **Request interceptor**: Tự động lấy JWT `idToken` từ Cognito session và gắn vào header `Authorization: Bearer <token>` cho mọi request.
  - **Response interceptor**: Tự động retry (tối đa 10 lần, mỗi lần cách 5 giây) khi gặp lỗi `503`, `504`, hoặc timeout — đây là cơ chế xử lý Lambda cold start.

- **`cognito.js`**: Khởi tạo `CognitoUserPool` với `Storage: sessionStorage` (mỗi tab trình duyệt có session độc lập, tránh xung đột multi-tab). Export hàm `getSessionToken()` để lấy JWT token hiện tại.

- **`services/smartdocService.js`**: Tập hợp toàn bộ API call cho tính năng RAG:
  - `checkStatus()` — GET `/api/status` (kiểm tra LLM online)
  - `getUploadUrl()` — POST `/api/upload-url` (lấy S3 presigned URL)
  - `uploadFileToS3()` — PUT trực tiếp lên S3 qua presigned URL
  - `processDocument()` — POST `/api/process` (chunking + embedding)
  - `getDocuments()` — GET `/api/files`
  - `deleteDocument()` / `clearDocuments()`
  - `sendMessage()` — POST `/api/chat`
  - `getChatHistory()` / `clearChatHistory()`

- **`services/profileService.js`**: API call quản lý hồ sơ người dùng:
  - `getProfile()` — GET `/api/profile`
  - `updatePersonalInfo()` — PUT `/api/profile/personal-info`
  - `updateAvatar()` — PUT `/api/profile/avatar` (base64, tự động chọn DynamoDB hay S3 ở backend)
  - `changePassword()` — POST `/api/profile/change-password`

---

#### `src/store/`
Quản lý state toàn cục bằng **Redux Toolkit**.

Store có 2 reducer chính:

- **`authSlice`**: Quản lý vòng đời xác thực:
  - `login` (async thunk) — Xác thực trực tiếp qua Cognito SDK, lưu user vào `sessionStorage`
  - `register` (async thunk) — Gọi backend API để tạo tài khoản và đồng bộ DynamoDB
  - `logout` (async thunk) — Sign out Cognito + xóa session
  - `getProfile` (async thunk) — Lấy thông tin đầy đủ từ DynamoDB (bao gồm avatar)
  - State: `user` (thông tin user), `isAuthenticated`, `loading`, `error`

- **`smartdocSlice`**: Quản lý toàn bộ state của tính năng RAG:
  - `checkOllamaStatus` — Kiểm tra trạng thái LLM backend
  - `fetchProcessedFiles` — Lấy danh sách tài liệu đã xử lý
  - `fetchChatHistory` — Lấy lịch sử hội thoại
  - `sendChatMessage` — Gửi câu hỏi và nhận phản hồi từ AI
  - `uploadAndProcessDocument` — Pipeline upload file: lấy presigned URL → upload S3 → trigger process
  - State: `ollamaStatus`, `processedFiles`, `chatHistory`, `messages`, `chunkSettings`...

> Xem `src/store/README.md` để hiểu chi tiết kỹ thuật `createSelector` và memoization.

---

#### `src/features/`
Tổ chức theo mô hình **Feature-Sliced Design** — mỗi tính năng là một module độc lập với `components/` và `pages/` riêng.

**`auth/`** — Xác thực:
- `LoginPage` / `RegisterPage`: Trang công khai, không cần đăng nhập.
- `ProtectedRoute`: HOC kiểm tra `isAuthenticated` từ Redux store; nếu chưa đăng nhập thì redirect về `/login`.

**`profile/`** — Hồ sơ cá nhân:
- `ProfilePage`: Trang có 2 tab — *Thông tin cá nhân* và *Bảo mật*.
- `ProfileAvatar`: Upload avatar (crop, resize, gửi base64).
- `PersonalInfoTab`: Chỉnh sửa tên, email, SĐT, ngày sinh.
- `SecurityTab`: Đổi mật khẩu.

**`smartdocs/`** — Tính năng chính RAG:
- `SmartdocPage`: Trang chính, ghép `SmartSidebar` và `ChatArea` theo layout 2 cột.
- `SmartSidebar` (layout): Sidebar có thể thu gọn (collapsible) trên desktop và dạng drawer overlay trên mobile. Chứa toàn bộ control: status LLM, upload file, danh sách file, cài đặt chunking, lịch sử chat, thông tin user + nút logout.
- `ChatArea` (chat): Khu vực hiển thị hội thoại. Khi chưa có chat thì hiển thị `WelcomeHero`. Mỗi tin nhắn AI có thể kèm `SourceCitationPanel` (nguồn trích dẫn) và metadata RAG (`SelfRagMetadata` / `CoRagMetadata`).

---

#### `src/contexts/`
- **`ThemeContext`**: Quản lý Dark/Light mode. Đọc preference từ `localStorage` và system preference khi khởi động. Toggle theme sẽ apply class `dark` lên `<html>` (tương thích Tailwind dark mode).

---

#### `src/components/`
- **`ui/`**: Toàn bộ component từ **Shadcn/ui** (button, card, dialog, select, tabs, toast...). Đây là các primitive component dựa trên Radix UI + Tailwind.
- **`common/`**: Component tiện ích tự viết dùng nhiều nơi: `Loading`, `LoadMore`, `FailedAlert`.

---

#### `src/lib/`
- **`utils.js`**: Export hàm `cn()` — kết hợp `clsx` và `tailwind-merge` để merge class Tailwind an toàn.
- **`helpers.js`**: Các hàm tiện ích: `formatDateToVNDate`, `buildCategoryById` (Map O(1)), `withCategory`, `calculatePercent`.
- **`alertUtils.js`**: Wrapper tiện ích hiển thị thông báo toast.
- **`goalUtils.js`**: Tiện ích tính toán liên quan đến mục tiêu.

---

## 3. LUỒNG DỮ LIỆU (Data Flow)

```
User Action
    │
    ▼
Component (dispatch action)
    │
    ▼
Redux Thunk (async thunk trong slice)
    │
    ├──► API Service (smartdocService / profileService)
    │         │
    │         ▼
    │    axiosClient (tự gắn Cognito JWT token)
    │         │
    │         ▼
    │    AWS API Gateway → Lambda → (S3 / DynamoDB / LLM)
    │         │
    │         ▼
    │    Response data
    │
    ▼
Redux Store (state updated)
    │
    ▼
React Component re-render (useSelector)
```

---

## 4. ROUTING

Routing được định nghĩa trong `App.jsx` sử dụng **React Router v7**:

| Path | Component | Loại |
|---|---|---|
| `/` | Redirect → `/login` | — |
| `/login` | `LoginPage` | Public |
| `/register` | `RegisterPage` | Public |
| `/app/*` | `SmartdocPage` (bọc trong `ProtectedRoute`) | Protected |
| `/app/profile` | `ProfilePage` (bọc trong `ProtectedRoute`) | Protected |

> **`ProtectedRoute`**: Kiểm tra `isAuthenticated` trong Redux store. Nếu chưa đăng nhập → redirect về `/login`.

---

## 5. CẤU HÌNH QUAN TRỌNG

### Vite Proxy (phát triển cục bộ)
`vite.config.js` cấu hình proxy `/api` → AWS API Gateway để tránh lỗi CORS khi chạy local:
```
http://localhost:5173/api/* → https://nxmlsvv3zk.execute-api.us-east-1.amazonaws.com/prod/*
```

### Path Alias
`@` được ánh xạ tới `src/`, giúp import gọn hơn:
```js
import { Button } from "@/components/ui/button";
// thay vì: ../../components/ui/button
```

### AWS Cognito — sessionStorage
Cognito được cấu hình dùng `sessionStorage` thay vì `localStorage` mặc định. Điều này đảm bảo mỗi tab trình duyệt có session độc lập, tránh lỗi multi-tenant khi đăng nhập các user khác nhau trên nhiều tab.

### CI/CD
File `buildspec.yml` dùng cho **AWS CodeBuild** để tự động build và deploy frontend lên S3/CloudFront khi có commit mới.