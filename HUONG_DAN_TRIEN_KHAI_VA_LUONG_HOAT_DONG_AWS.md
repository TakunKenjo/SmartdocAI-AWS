# HƯỚNG DẪN TRIỂN KHAI VÀ LUỒNG HOẠT ĐỘNG CỦA SMARTDOCAI TRÊN AWS

Tài liệu này giải thích chi tiết **Luồng hoạt động hệ thống (Architecture & Workflow)** và **Hướng dẫn các bước triển khai (Deployment Guide)** cho đồ án **SmartDocAI** trên hạ tầng Điện toán đám mây Amazon Web Services (AWS) với những cập nhật tối ưu hóa hiệu năng mới nhất, tích hợp hệ thống xác thực người dùng AWS Cognito & lưu trữ DynamoDB.

---

## MỤC LỤC
1. [Tổng quan Kiến trúc Hệ thống (Architecture Overview)](#1-tổng-quan-kiến-trúc-hệ-thống-architecture-overview)
2. [Luồng Hoạt động Chi tiết (Detailed Workflows)](#2-luồng-hoạt-động-chi-tiết-detailed-workflows)
   - [Luồng 1: Khởi tạo & Đánh thức Serverless (Warm-up)](#luồng-1-khởi-tạo--đánh-thức-serverless-warm-up)
   - [Luồng 2: Xác thực & Quản lý Người dùng qua AWS Cognito (User Authentication)](#luồng-2-xác-thực--quản-ly-người-dùng-qua-aws-cognito-user-authentication)
   - [Luồng 3: Tải lên và Phân tích Tài liệu 3 Bước qua S3 Presigned URL (Upload & Indexing)](#luồng-3-tải-lên-và-phân-tích-tài-liệu-3-bước-qua-s3-presigned-url-upload--indexing)
   - [Luồng 4: Hỏi đáp RAG thông minh (Retrieval-Augmented Generation)](#luồng-4-hỏi-đáp-rag-thông-minh-retrieval-augmented-generation)
   - [Luồng 5: Đồng bộ hóa Trạng thái đa Container (Serverless State Synchronization)](#luồng-5-đồng-bộ-hóa-trạng-thái-đa-container-serverless-state-synchronization)
3. [Hướng dẫn Triển khai Từ đầu lên AWS (Step-by-Step Deployment Guide)](#3-hướng-dẫn-triển-khai-từ-đầu-lên-aws-step-by-step-deployment-guide)
4. [Hướng dẫn Chạy Dự án trên Máy mới (Clone từ Git)](#4-hướng-dẫn-chạy-dự-án-trên-máy-mới-clone-từ-git)
5. [Các Điểm Tối ưu Kỹ thuật Đột phá (Key Performance Innovations)](#5-các-điểm-tối-ưu-kỹ-thuật-đột-phá-key-performance-innovations)

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG (ARCHITECTURE OVERVIEW)

SmartDocAI sử dụng mô hình **Serverless Container Architecture** hoàn toàn trên AWS để tối ưu hóa chi phí (chỉ tính tiền khi có request), khả năng tự động mở rộng (auto-scaling) và tính sẵn sàng cao.

### Sơ đồ Khối Hệ thống (Mermaid Diagram):

```mermaid
flowchart TD
    subgraph Client ["Trình duyệt Người dùng (Client)"]
        UI["React.js + Vite (Single Page App)"]
    end

    subgraph AWS_Cloud ["Hạ tầng AWS Cloud (us-east-1)"]
        Cognito["AWS Cognito User Pool\n(User Auth & JWT)"]
        DynamoDB["Amazon DynamoDB\n(User Profiles / Metadata)"]
        APIGW["AWS API Gateway\n(HTTP API /prod)"]
        
        subgraph Lambda_Container ["AWS Lambda (Docker Image tag 5.5)"]
            FastAPI["FastAPI App\n(app_api.py)"]
            RAG["RAG Chain Engine\n(rag_chain.py)"]
            DocProc["Document Processor\n(document_processor.py - pypdf)"]
            ParallelEmbed["Parallel Bedrock Embeddings\n(12 Thread Workers)"]
        end
        
        S3["Amazon S3 Bucket\n(smartdocai-storage-...)\n- Raw PDF/DOCX\n- FAISS Index (1024-dim)\n- Metadata (chat_history, files)"]
        Bedrock_Titan["AWS Bedrock Titan Embeddings V2\n(amazon.titan-embed-text-v2:0)"]
        Bedrock_LLM["Amazon Bedrock Runtime\n(Qwen 3 Next 80B - qwen.qwen3-next-80b-a3b)"]
    end

    UI -->|1. Register / Login / Verify| Cognito
    Cognito <-->|Sync Profile| DynamoDB
    UI -->|2. Request Presigned URL\n(Bearer JWT Token)| APIGW
    APIGW -->|Proxy| FastAPI
    UI -->|3. Direct PUT Binary Upload| S3
    UI -->|4. POST /api/process\n(Bearer JWT Token)| APIGW
    FastAPI --> DocProc
    DocProc -->|Parallel Vectorizing| ParallelEmbed
    ParallelEmbed -->|Invoke API| Bedrock_Titan
    DocProc -->|Sync Index & Files| S3
    
    UI -->|POST /api/chat\n(Bearer JWT Token)| APIGW
    FastAPI --> RAG
    RAG -->|Read Index & Metadata| S3
    RAG -->|Invoke LLM| Bedrock_LLM
```

### Các Thành phần Chính trong Hạ tầng:
1. **Frontend (React + Vite)**: Giao diện người dùng hiện đại, quản lý state với Redux Toolkit, bảo vệ các route nghiệp vụ qua `ProtectedRoute` liên kết trực tiếp với AWS Cognito. Tích hợp cơ chế **Silent Background Auto-Retry** tự động gửi lại request ngầm khi server bận.
2. **AWS Cognito User Pool**: Hệ thống quản lý thông tin và xác thực người dùng hoàn chỉnh. Đảm nhiệm chức năng đăng ký, xác thực mã OTP qua Email, đăng nhập và cung cấp JWT Token bảo mật.
3. **Amazon DynamoDB**: Cơ sở dữ liệu NoSQL lưu giữ thông tin hồ sơ (User Profiles) và siêu dữ liệu bổ sung của người dùng, liên kết đồng bộ hóa với Cognito.
4. **AWS API Gateway (HTTP API)**: Điểm tiếp nhận request HTTPS từ Frontend, tự động định tuyến (Proxy Routing `/{proxy+}`) sang AWS Lambda, truyền kèm mã JWT Token dưới dạng Header `Authorization: Bearer <Token>`.
5. **AWS Lambda (Docker Container Image)**: Nơi thực thi logic Backend Python (FastAPI). Sử dụng Docker Image tối ưu siêu nhẹ (~1.0 GB) **không chứa PyTorch hay Weights cục bộ**.
6. **Amazon S3 (Simple Storage Service)**: Bộ lưu trữ đám mây persistent dùng để lưu các file tài liệu gốc qua Presigned URL, bộ chỉ mục vector **FAISS (1024 chiều)**, lịch sử cuộc trò chuyện (`chat_history.json`) và danh sách file đã xử lý (`processed_files.json`).
7. **AWS Bedrock Titan Embeddings V2 (`amazon.titan-embed-text-v2:0`)**: Dịch vụ nhúng vector đám mây 1024 chiều thay thế mô hình LaBSE cục bộ, giúp triệt tiêu hoàn toàn thời gian tải model lúc Cold Start.
8. **Amazon Bedrock LLM Qwen 3 Next 80B (`qwen.qwen3-next-80b-a3b`)**: Mô hình ngôn ngữ thế hệ mới hiệu năng cao trên Bedrock phục vụ tổng hợp câu trả lời RAG với tính chính xác cao kèm trích dẫn nguồn chuẩn xác.

---

## 2. LUỒNG HOẠT ĐỘNG CHI TIẾT (DETAILED WORKFLOWS)

### Luồng 1: Khởi tạo & Đánh thức Serverless (Warm-up)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant App as React Frontend
    participant GW as API Gateway
    participant Lambda as AWS Lambda
    
    User->>App: Mở ứng dụng trên trình duyệt
    App->>GW: Gửi GET /api/status (Tự động kiểm tra trạng thái)
    alt Lambda đang ở trạng thái Cold Start (Tắt)
        GW->>Lambda: Khởi chạy Docker Container mới
        Lambda->>Lambda: Nạp FastAPI App & Bedrock SDK (Init: < 1.0s)
        Lambda-->>GW: Trả về HTTP 200 { model_ready: true }
    else Lambda đang ở trạng thái Warm (Ấm)
        Lambda-->>GW: Trả về HTTP 200 ngay lập tức (< 0.05s)
    end
    GW-->>App: Trả về trạng thái kết nối hệ thống sẵn sàng
```

---

### Luồng 2: Xác thực & Quản lý Người dùng qua AWS Cognito (User Authentication)

Quy trình đăng ký, xác thực tài khoản qua mã OTP Email và đăng nhập bảo mật của hệ thống:

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant App as React Frontend
    participant Cognito as AWS Cognito User Pool
    participant Dynamo as Amazon DynamoDB
    
    rect rgb(240, 248, 255)
        note right of App: Quy trình Đăng ký (Register)
        User->>App: Nhập Email, Password, Fullname, Phone, DOB
        App->>Cognito: Gọi signUp() (Định dạng SĐT E.164)
        Cognito-->>App: Trả về trạng thái chờ xác thực (User Confirmed = False)
        Cognito->>User: Gửi Email chứa mã xác thực (OTP Code)
        User->>App: Nhập mã OTP
        App->>Cognito: Gọi confirmRegistration(code)
        Cognito->>Cognito: Xác thực OTP thành công (User Confirmed = True)
        opt Trigger Post-Confirmation
            Cognito->>Dynamo: Tự động sync thông tin profile của user mới
        end
        Cognito-->>App: Đăng ký hoàn tất
    end
    
    rect rgb(255, 245, 238)
        note right of App: Quy trình Đăng nhập (Login)
        User->>App: Nhập Email & Password
        App->>Cognito: Gọi authenticateUser()
        Cognito->>Cognito: Kiểm tra credentials & Tạo JWT Token
        Cognito-->>App: Trả về ID Token, Access Token & Refresh Token
        App->>App: Lưu User Profile vào sessionStorage & Redux State
    end
```

---

### Luồng 3: Tải lên và Phân tích Tài liệu 3 Bước qua S3 Presigned URL (Upload & Indexing)

Để vượt qua giới hạn dung lượng **10 MB** của AWS API Gateway và khắc phục triệt để lỗi `413 Request Entity Too Large`, SmartDocAI sử dụng quy trình tải lên 3 bước qua S3 Presigned URL, có đính kèm Authorization Header:

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as React UI
    participant GW as API Gateway
    participant Lambda as AWS Lambda Engine
    participant S3 as Amazon S3 Storage
    participant Titan as AWS Bedrock Titan Embeddings V2
    
    User->>UI: Kéo thả file (.pdf / .docx) & nhấn "Tải lên"
    
    rect rgb(240, 248, 255)
        note right of UI: Bước 1: Xin cấp quyền Upload (Kèm Cognito JWT Token)
        UI->>GW: POST /api/upload-url { filename, content_type } (Authorization Header)
        GW->>Lambda: Tạo S3 Presigned PUT URL (Hạn dùng 15 phút)
        Lambda-->>UI: Trả về { upload_url, s3_key }
    end
    
    rect rgb(255, 245, 238)
        note right of UI: Bước 2: Tải file trực tiếp lên S3 (Bỏ qua API Gateway)
        UI->>S3: HTTP PUT [upload_url] (Hỗ trợ file lên tới 5 GB)
        S3-->>UI: HTTP 200 OK (Upload S3 hoàn tất)
    end
    
    rect rgb(240, 255, 240)
        note right of UI: Bước 3: Kích hoạt phân tích & nhúng Vector (Kèm JWT Token)
        UI->>GW: POST /api/process { filename, s3_key } (Authorization Header)
        GW->>Lambda: Chuyển tiếp yêu cầu xử lý
        Lambda->>S3: Tải file từ s3_key về /tmp
        Lambda->>Lambda: Trích xuất văn bản siêu tốc bằng pypdf (0.3s cho 256 trang)
        Lambda->>Lambda: Chia nhỏ văn bản (RecursiveCharacterTextSplitter)
        Lambda->>Titan: Tạo Vector 1024 chiều qua Parallel Bedrock Embeddings (12 workers song song)
        Lambda->>Lambda: Tạo/Cập nhật Chỉ mục FAISS Vector Store
        Lambda->>S3: Sync index.faiss & index.pkl lên S3 (vectorstore/smartdoc_index/)
        Lambda->>S3: Cập nhật processed_files.json
        Lambda-->>UI: Trả về JSON: status success, số trang & số chunks
    end
    GW-->>UI: Hiển thị danh sách tài liệu đã xử lý thành công
```

---

### Luồng 4: Hỏi đáp RAG thông minh (Retrieval-Augmented Generation)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant UI as React UI
    participant GW as API Gateway
    participant Lambda as AWS Lambda RAG Chain
    participant S3 as Amazon S3
    participant Bedrock as Amazon Bedrock (Qwen 3 Next 80B)
    
    User->>UI: Nhập câu hỏi (VD: "Tóm tắt tài liệu")
    UI->>GW: POST /api/chat { message: "tóm tắt tài liệu" } (Authorization Header)
    GW->>Lambda: Gọi hàm ask_question()
    
    Lambda->>S3: Đọc danh sách file & FAISS index từ S3 về /tmp (Nếu có cập nhật)
    
    alt Loại câu hỏi Tóm tắt (Summary Query)
        Lambda->>Lambda: Chọn 12 chunks phân bổ đều trải dài từ đầu đến cuối sách
    else Câu hỏi tra cứu cụ thể (Specific Question)
        Lambda->>Lambda: Tìm kiếm Vector tương đồng 1024-dim (FAISS / Hybrid Search)
    end
    
    Lambda->>Lambda: Trích xuất Context + Lịch sử Chat + Prompt
    Lambda->>Bedrock: Gọi invoke_model() tới Qwen 3 Next 80B
    Bedrock-->>Lambda: Trả về văn bản câu trả lời hoàn chỉnh
    Lambda->>Lambda: Tự động trích lấy Nguồn (File, Trang) từ Metadata trong RAM (< 0.1ms)
    Lambda->>S3: Lưu tin nhắn mới vào chat_history.json trên S3
    Lambda-->>GW: Trả về JSON { answer: "...", sources: [...] }
    GW-->>UI: Renders câu trả lời & Nguồn trích dẫn (Citations)
```

---

### Luồng 5: Đồng bộ hóa Trạng thái đa Container (Serverless State Synchronization)

Do môi trường AWS Lambda hoạt động theo cơ chế **vô trạng thái (Stateless)**, nhiều Warm Container có thể chạy song song. Để tránh lỗi lệch dữ liệu:
* **Không phụ thuộc vào biến RAM tĩnh**: Mọi thao tác ghi (xóa tài liệu, xóa chat, upload mới) đều trực tiếp cập nhật lên **Amazon S3**.
* **So sánh trước khi truy vấn**: Mọi request truy vấn RAG đều kiểm tra dấu vân tay (ETag/Timestamp) của file trên S3 với dữ liệu trong `/tmp`. Nếu phát hiện có sự thành đổi, container sẽ tự động dọn cache cũ và tải chỉ mục FAISS mới nhất từ S3 về.

---

## 3. HƯỚNG DẪN TRIỂN KHAI TỪ ĐẦU LÊN AWS (STEP-BY-STEP DEPLOYMENT GUIDE)

### Các Tiền đề Cần chuẩn bị:
1. Tài khoản AWS active (Khu vực khuyến nghị: `us-east-1` N. Virginia).
2. [AWS CLI](https://aws.amazon.com/cli/) đã cài đặt và cấu hình (`aws configure`).
3. [Docker Desktop](https://www.docker.com/) đã chạy trên máy cá nhân.
4. Python 3.11 & Node.js 18+.

---

### BƯỚC 1: Tạo Amazon S3 Bucket & Cấu hình CORS
Chạy lệnh CLI sau để tạo bucket lưu trữ dữ liệu và bật CORS cho phép Upload trực tiếp từ trình duyệt:
```powershell
# 1. Tạo bucket S3
aws s3api create-bucket --bucket smartdocai-storage-623035187993 --region us-east-1

# 2. Tạo file cors.json
@'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}
'@ | Out-File -Encoding utf8 cors.json

# 3. Apply CORS Policy lên S3 Bucket
aws s3api put-bucket-cors --bucket smartdocai-storage-623035187993 --cors-configuration file://cors.json
```

---

### BƯỚC 2: Tạo IAM Role cho AWS Lambda
1. Lưu nội dung trust policy vào file `trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
2. Tạo IAM Role tên là `smartdocai-lambda-role`:
```powershell
aws iam create-role --role-name smartdocai-lambda-role --assume-role-policy-document file://trust-policy.json
```
3. Đính kèm các quyền AWS quản lý:
```powershell
# Quyền ghi log CloudWatch
aws iam attach-role-policy --role-name smartdocai-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Quyền toàn quyền thao tác S3
aws iam attach-role-policy --role-name smartdocai-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Quyền truy cập Amazon Bedrock Runtime (Titan Embeddings + Qwen LLM)
aws iam attach-role-policy --role-name smartdocai-lambda-role --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

---

### BƯỚC 3: Tạo và Thiết lập AWS Cognito User Pool & DynamoDB Table
Để quản lý xác thực người dùng, bạn cần tạo User Pool trong dịch vụ Cognito và bảng DynamoDB để lưu trữ siêu dữ liệu.

1. **Khởi tạo Cognito User Pool**:
   - Truy cập vào AWS Console -> Amazon Cognito -> **Create user pool**.
   - Chọn thuộc tính đăng nhập (**Sign-in experience**): Chọn **Email** (Cho phép đăng nhập bằng email).
   - Chọn các thuộc tính bắt buộc (**Required attributes**):
     - `email`
     - `name` (Dành cho Fullname)
     - `phone_number`
     - `birthdate`
   - Cấu hình mật khẩu và phương thức xác minh: Chọn **Self-service sign-up** (Người dùng tự đăng ký) và gửi mã xác thực xác minh (Verification code) qua **Email**.
   - Tạo **App client**: Chọn loại Single Page Application (SPA), đặt tên client (VD: `smartdocai-client`). **Lưu ý tắt "Generate client secret"** vì SDK client-side không sử dụng secret key này.
   - Nhận diện các giá trị:
     - `User Pool ID` (Ví dụ: `us-east-1_3oq5wIiuu`)
     - `Client ID` (Ví dụ: `63f74h4dj78kqihhoimv4acl8a`)

2. **Khởi tạo Amazon DynamoDB Table**:
   - Truy cập AWS Console -> DynamoDB -> **Create table**.
   - Đặt tên bảng: `smartdocai-users` (hoặc bảng cấu hình tùy chọn để đồng bộ profile).
   - Partition key: `email` (String) hoặc `userId` (String).
   - Cấu hình Provisioned/On-Demand capacity tùy nhu cầu chi phí (On-demand khuyến nghị cho serverless).

---

### BƯỚC 4: Đóng gói và Push Docker Image lên AWS ECR

1. **Tạo ECR Repository**:
```powershell
aws ecr create-repository --repository-name smartdocai --region us-east-1
```

2. **Build Docker Image** (tại thư mục `backend`):
```powershell
cd backend
docker build --provenance=false -t 623035187993.dkr.ecr.us-east-1.amazonaws.com/smartdocai:5.5 .
```

3. **Đăng nhập Docker vào ECR**:
```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 623035187993.dkr.ecr.us-east-1.amazonaws.com
```

4. **Push Docker Image lên ECR**:
```powershell
docker push 623035187993.dkr.ecr.us-east-1.amazonaws.com/smartdocai:5.5
```

---

### BƯỚC 5: Triển khai AWS Lambda Function

1. **Tạo Hàm Lambda từ Container Image**:
```powershell
aws lambda create-function `
  --function-name smartdocai `
  --package-type Image `
  --code ImageUri=623035187993.dkr.ecr.us-east-1.amazonaws.com/smartdocai:5.5 `
  --role arn:aws:iam::623035187993:role/smartdocai-lambda-role `
  --timeout 300 `
  --memory-size 3008 `
  --region us-east-1
```

---

### BƯỚC 6: Triển khai AWS API Gateway (HTTP API)

1. **Tạo HTTP API Gateway**:
```powershell
aws apigatewayv2 create-api `
  --name smartdocai-api `
  --protocol-type HTTP `
  --target arn:aws:lambda:us-east-1:623035187993:function:smartdocai `
  --region us-east-1
```

2. **Cấp quyền cho API Gateway gọi Lambda**:
```powershell
aws lambda add-permission `
  --function-name smartdocai `
  --statement-id apigateway-access `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com `
  --region us-east-1
```

*Đường dẫn API thu được có dạng*: `https://d60866voq5.execute-api.us-east-1.amazonaws.com/prod`

---

### BƯỚC 7: Cấu hình và Triển khai Frontend

1. Chuyển đến thư mục frontend: `cd smart-docs-ai/smart-docs-ai`
2. Mở file [vite.config.js](file:///c:/Users/Flow/Desktop/projects/SmartdocAI-AWS/smart-docs-ai/smart-docs-ai/vite.config.js) để cấu hình định nghĩa `global` và proxy API:
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    // Định nghĩa global là window để amazon-cognito-identity-js chạy ổn định trên browser
    global: 'window',
  },
  server: {
    watch: {
      ignored: ['**/db.json', '**/db/**']
    },
    proxy: {
      '/api': {
        target: 'https://d60866voq5.execute-api.us-east-1.amazonaws.com/prod',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path,
        // Timeout 3 phút phù hợp thời gian chờ Lambda Cold Start tối đa
        proxyTimeout: 180000,
        timeout: 180000,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('[Vite Proxy Error]', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req) => {
            console.log('[Vite Proxy]', req.method, req.url, '→ AWS Lambda');
          });
        },
      }
    }
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    }
  }
})
```
3. Cấu hình thông tin AWS Cognito trong file [cognito.js](file:///c:/Users/Flow/Desktop/projects/SmartdocAI-AWS/smart-docs-ai/smart-docs-ai/src/api/cognito.js):
```javascript
import { CognitoUserPool } from "amazon-cognito-identity-js";

const poolData = {
  UserPoolId: "us-east-1_3oq5wIiuu", // ID của User Pool bạn vừa tạo ở Bước 3
  ClientId: "63f74h4dj78kqihhoimv4acl8a",   // Client ID của App Client ở Bước 3
};

export const userPool = new CognitoUserPool(poolData);
```
4. Khởi chạy ứng dụng Frontend local:
```powershell
npm install
npm run dev
```

---

## 4. HƯỚNG DẪN CHẠY DỰ ÁN TRÊN MÁY MỚI (CLONE TỪ GIT)

Khi clone dự án về một máy tính khác, bạn có 2 sự lựa chọn:

### Trường hợp A: Dùng chung Backend AWS hiện tại (Nhanh nhất - Không cần cài Python/Docker)
1. Cài đặt Node.js trên máy mới.
2. Clone repository từ Github về máy.
3. Mở terminal tại thư mục `smart-docs-ai/smart-docs-ai`:
   ```bash
   npm install
   npm run dev
   ```
4. Truy cập `http://localhost:5173`. Frontend trên máy mới sẽ kết nối trực tiếp với API Gateway trên AWS đã dựng sẵn và xác thực tài khoản qua Cognito.

---

### Trường hợp B: Chạy Backend Local phát triển (Hot-Reload)
1. Cài đặt Python 3.11 & Docker.
2. Tạo file `.env` tại thư mục `backend` chứa AWS Access Keys có quyền kết nối Bedrock & S3:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=us-east-1
   S3_BUCKET=smartdocai-storage-623035187993
   ```
3. Khởi chạy Backend FastAPI Local:
   ```bash
   cd backend
   pip install -r requirements.txt
   python run.py
   ```
4. Đổi `target` trong [vite.config.js](file:///c:/Users/Flow/Desktop/projects/SmartdocAI-AWS/smart-docs-ai/smart-docs-ai/vite.config.js) thành `http://localhost:8000`.

---

## 5. CÁC ĐIỂM TỐI ƯU KỸ THUẬT ĐỘT PHÁ (KEY PERFORMANCE INNOVATIONS)

1. **Bảo mật và Xác thực Tự động (Cognito JWT Interceptor)**:
   - Tích hợp Cognito JWT Token trực tiếp vào Header của mọi request thông qua Axios Interceptor, đảm bảo tất cả các API nghiệp vụ chính đều được bảo vệ và kiểm soát quyền truy cập chặt chẽ ở cấp độ hạ tầng.

2. **Khắc phục triệt để lỗi 413 Payload Too Large (S3 Presigned URL Direct Upload)**:
   - Thay thế việc gửi file qua API Gateway bằng cơ chế Presigned URL 3 bước. Người dùng upload file trực tiếp từ trình duyệt lên S3 Bucket mà không thông qua API Gateway, hỗ trợ tệp dung lượng cực lớn lên tới **5 GB** với tốc độ truyền tải tối đa.

3. **Chuyển đổi Mô hình Nhúng AWS Bedrock Titan V2 (Triệt tiêu Cold Start)**:
   - Thay thế mô hình LaBSE cục bộ nặng 470MB bằng `amazon.titan-embed-text-v2:0` (API call đám mây, 1024 chiều).
   - Loại bỏ hoàn toàn `PyTorch` và `SentenceTransformers` khỏi Docker Image:
     - **Dung lượng Docker Image**: Giảm từ `2.5 GB` xuống `~1.0 GB` (Giảm 60%).
     - **Bộ nhớ RAM sử dụng**: Giảm từ `1295 MB` xuống `227 MB` (Giảm 82.5%).
     - **Thời gian Cold Start**: Giảm từ `146s` xuống **chưa tới 1 giây**.

4. **Cơ chế Nhúng Đa luồng Song song (Parallel Bedrock Embeddings)**:
   - Tích hợp `ThreadPoolExecutor` with **12 luồng xử lý song song** gọi đồng thời tới Bedrock Embeddings API.
   - Xử lý một cuốn sách **256 trang (426 chunks)** chỉ mất **16 giây** (nhanh gấp **3 lần** so với gọi tuần tự thông thường).

5. **Trích xuất Văn bản PDF Siêu tốc với `pypdf`**:
   - Sử dụng `pypdf` làm bộ trích xuất văn bản chính (fallback sang `pdfplumber`). Tốc độ đọc file PDF 256 trang giảm từ **38.5 giây xuống chỉ còn 0.3 giây** (Nhanh gấp **250 lần**).

6. **Trích xuất Nguồn trích dẫn (Citations) tức thì (< 0.1ms)**:
   - Thông tin Nguồn (Tên file, Trang) được trích xuất trực tiếp từ Metadata của Vector Store trong RAM bằng vòng lặp Python cực nhẹ, không làm tốn chút thời gian sinh văn bản nào của mô hình AI.

7. **Tự động Thử lại Ngầm (Silent Background Auto-Retry)**:
   - Axios Interceptor tự động bắt lỗi ngắt kết nối tạm thời 503/504 và thử lại ngầm 10 lần (mỗi 5s), giúp đảm bảo trải nghiệm của người dùng mượt mà ngay cả khi Lambda Container đang khởi động lại (Cold Start).
