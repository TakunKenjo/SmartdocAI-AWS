# Logs AdminLink Google Login - 2026-07-18

## Muc tieu

Hoan tat phase lien ket tai khoan Google OAuth voi user Cognito native da ton tai bang `AdminLinkProviderForUser`, tranh tao duplicate user cung email va giu nguyen du lieu theo `sub` cu.

## Branch va commit lien quan

- Branch lam viec: `phuc-google-login`
- Remote branch: `origin/phuc`
- Da merge production qua `origin/main`
- Commit chinh tren `origin/phuc`:
  - `a61b2852 feat: link Google sign-in to native Cognito users`
  - `4fc2b713 chore: store presignup lambda at deployable handler path`
  - `34791c7f chore: remove tracked Python cache files`
- Commit chinh tren `origin/main`:
  - `28b53353 merge: deploy Google Cognito account linking`
  - `27fb77dc chore: remove tracked Python cache files`

## Thay doi da thuc hien

### 1. Cognito PreSignUp Lambda

- Function AWS: `smartdocai-presignup-check`
- Runtime: `python3.12`
- Handler: `lambda_function.lambda_handler`
- Source da dua vao repo tai: `backend/lambdas/presignup_check/lambda_function.py`

Logic moi:

- Voi `PreSignUp_ExternalProvider`:
  - Doc email tu event Google OAuth.
  - Tim native Cognito user co cung email, username native dang la email.
  - Neu tim thay native user, goi `admin_link_provider_for_user` de link Google identity vao native user.
  - Set `autoConfirmUser = true` va `autoVerifyEmail = true`.
  - Neu email moi chua co native user, cho Google signup/login binh thuong.

- Voi `PreSignUp_SignUp`:
  - Neu email da ton tai o Google-only user va chua co native user, chan native signup voi message: `Email nay da duoc dang nhap bang Google. Vui long dang nhap bang Google.`
  - Cac case khac cho di tiep.

### 2. IAM cho PreSignUp Lambda

Role: `smartdocai-presignup-role`

Da cap quyen tren user pool `us-east-1_3oq5wIiuu`:

- `cognito-idp:ListUsers`
- `cognito-idp:AdminLinkProviderForUser`

IAM simulation da tra ve:

- `cognito-idp:ListUsers`: `allowed`
- `cognito-idp:AdminLinkProviderForUser`: `allowed`

### 3. Backend profile update

File: `backend/app_api.py`

Da them helper `extract_cognito_username_from_token()` de lay dung Cognito username tu JWT:

- Uu tien claim `cognito:username`.
- Fallback sang `email` neu token khong co `cognito:username`.

Endpoint `PUT /api/profile/personal-info` da doi tu:

```python
current_username = extract_email_from_token(authorization)
```

sang:

```python
current_username = extract_cognito_username_from_token(authorization)
```

Ly do: Google/federated user co Cognito username dang `Google_xxx`, khong phai email. Neu dung email de goi Cognito `admin_update_user_attributes`, profile update co the fail hoac update sai user.

### 4. Repository hygiene

- Da xoa cac file Python cache bi track nham:
  - `backend/__pycache__/*.pyc`
  - `backend/modules/__pycache__/*.pyc`
- `.gitignore` da co san rule:
  - `__pycache__/`
  - `*.pyc`

## Deploy da thuc hien

### PreSignUp Lambda

Da package va deploy function `smartdocai-presignup-check` bang AWS CLI.

Trang thai sau deploy:

- Function: `smartdocai-presignup-check`
- Handler: `lambda_function.lambda_handler`
- `LastUpdateStatus`: `Successful`
- `State`: `Active`
- Last modified: `2026-07-18T04:17:31.000+0000`

### Backend production Lambda

Da merge branch `origin/phuc` vao `main`, push `main` de CodePipeline backend tu dong deploy.

Pipeline:

- Name: `smartdocai-be-pipeline`
- Execution moi nhat: `Succeeded`
- Revision moi nhat: `27fb77dc3d4839e1af813cdf21c0ab33017b79e3`

Main Lambda sau deploy:

- Function: `smartdocai`
- `LastUpdateStatus`: `Successful`
- `State`: `Active`
- Last modified: `2026-07-18T04:26:32.000+0000`

## Ghi chu thao tac AWS da thuc hien

Tat ca thao tac AWS trong phase nay duoc thuc hien bang AWS CLI tu local terminal, khong thao tac truc tiep tren AWS Console UI.

### IAM

- Kiem tra inline policy hien co cua role `smartdocai-presignup-role`.
- Cap nhat inline policy `AllowListUsersForDuplicateEmailCheck` cho role `smartdocai-presignup-role`.
- Them action `cognito-idp:AdminLinkProviderForUser` ben canh action cu `cognito-idp:ListUsers`.
- Scope resource vao user pool:
  - `arn:aws:cognito-idp:us-east-1:623035187993:userpool/us-east-1_3oq5wIiuu`
- Chay IAM simulation de xac nhan ca hai action deu `allowed`.

### Cognito User Pool

- User pool lien quan: `us-east-1_3oq5wIiuu`.
- Kiem tra va dung PreSignUp trigger hien co: `smartdocai-presignup-check`.
- Khong tao user production that nao cho test.
- Co tao mot native Cognito user tam voi email dang `smartdocai-adminlink-test-<id>@example.com` de validate AdminLink.
- Sau khi xac nhan attribute `identities` co provider `Google`, da xoa user tam bang `admin-delete-user`.

### Lambda PreSignUp Trigger

- Download code hien tai cua function `smartdocai-presignup-check` de doc logic cu truoc khi thay.
- Logic cu: neu Google login trung native email thi raise exception va chan login.
- Logic moi: neu Google login trung native email thi goi `admin_link_provider_for_user` de link vao native user.
- Package source thanh zip co `lambda_function.py` o root.
- Deploy bang `aws lambda update-function-code` cho function `smartdocai-presignup-check`.
- Kiem tra sau deploy bang `aws lambda get-function-configuration`:
  - Handler: `lambda_function.lambda_handler`
  - Runtime: `python3.12`
  - State: `Active`
  - LastUpdateStatus: `Successful`
- Invoke synthetic event de xac nhan runtime khong loi import/handler.

### CodePipeline va CodeBuild

- Push `main` de trigger pipeline backend `smartdocai-be-pipeline`.
- Kiem tra execution bang `aws codepipeline list-pipeline-executions`.
- Kiem tra stage bang `aws codepipeline get-pipeline-state`.
- Lay CodeBuild external execution id tu action `Build`.
- Kiem tra build bang `aws codebuild batch-get-builds`.
- Doc CloudWatch logs cua CodeBuild khi build dang chay bang `aws logs get-log-events`.
- Ket qua cuoi:
  - Source stage: `Succeeded`
  - Build stage: `Succeeded`
  - Pipeline execution moi nhat: `Succeeded`

### Lambda Backend Production

- CodePipeline build va deploy image moi cho Lambda `smartdocai`.
- Kiem tra sau deploy bang `aws lambda get-function-configuration`:
  - Function: `smartdocai`
  - State: `Active`
  - LastUpdateStatus: `Successful`
- Goi smoke test API Gateway production root de xac nhan Lambda khong crash luc import/startup.

### CloudWatch Logs

- Dung CloudWatch Logs cua CodeBuild de theo doi build Docker image backend.
- PreSignUp Lambda runtime test tra `StatusCode=200`, `FunctionError=None`, nen khong can debug traceback Lambda trong phase nay.

## Test va validation da chay

### 1. Python syntax compile

Da chay:

```powershell
C:/msys64/ucrt64/bin/python.exe -m py_compile backend/app_api.py backend/lambdas/presignup_check/lambda_function.py
```

Ket qua: pass, khong co output loi.

### 2. Frontend build

Da chay:

```powershell
npm run build
```

Tai thu muc:

```text
smart-docs-ai/smart-docs-ai
```

Ket qua: build thanh cong.

Ghi chu: Vite co warning chunk JS lon hon 500 kB, nhung day la warning ve toi uu bundle, khong phai loi build.

### 3. PreSignUp Lambda synthetic invoke

Da invoke `smartdocai-presignup-check` voi event `PreSignUp_SignUp` email gia:

- StatusCode: `200`
- FunctionError: `None`
- Output tra lai event goc.

Muc dich: xac nhan zip deploy dung layout `lambda_function.py` o root va handler import duoc.

### 4. AdminLinkProviderForUser test bang Cognito temp user

Da test end-to-end co kiem soat:

1. Tao native Cognito user tam voi email dang:
   - `smartdocai-adminlink-test-<id>@example.com`
2. Set password tam de user o trang thai native usable.
3. Invoke PreSignUp Lambda voi:
   - `triggerSource = PreSignUp_ExternalProvider`
   - `userName = Google_test-google-sub-<id>`
   - cung email voi native user tam.
4. Lambda tra ve:
   - `autoConfirmUser = true`
   - `autoVerifyEmail = true`
5. Goi `admin-get-user` cho native user, thay attribute `identities` co provider `Google`:

```json
[
  {
    "providerName": "Google",
    "providerType": "Google",
    "primary": "false"
  }
]
```

6. Da xoa native user tam sau test.

Ket qua: AdminLinkProviderForUser hoat dong dung voi native user trung email.

### 5. CodePipeline backend

Da kiem tra `smartdocai-be-pipeline` sau khi push `main`.

Ket qua:

- Execution cho commit merge AdminLink: `Succeeded`
- Execution cho commit cleanup cache: `Succeeded`
- Source stage: `Succeeded`
- Build stage: `Succeeded`

### 6. Production API smoke test

Da goi API Gateway production root:

```text
https://nxmlsvv3zk.execute-api.us-east-1.amazonaws.com/prod/
```

Ket qua: HTTP `404`.

Giai thich: root route khong ton tai nen `404` la expected. Diem quan trong la Lambda import/startup khong crash.

## Viec chua the tu dong test het

Chua test duoc login Google that bang browser/tai khoan Google cua user vi luong OAuth can phien browser va Google account that.

Can test thu cong:

1. Lay mot email da co native Cognito account.
2. Dang nhap bang Google cung email do.
3. Ky vong:
   - Khong bi block duplicate email.
   - Khong tao duplicate profile/DynamoDB user moi.
   - Token sau login tro ve user da link.
   - Du lieu cu theo native `sub` van con.
4. Thu update profile sau Google login.
5. Ky vong endpoint `PUT /api/profile/personal-info` khong con loi Cognito username mismatch.

## Ket luan

Phase ha tang va backend cho Google account linking da hoan tat:

- IAM da du quyen.
- PreSignUp Lambda da live va runtime-tested.
- AdminLinkProviderForUser da duoc validate bang Cognito temp user.
- Backend profile update fix da deploy production.
- CodePipeline backend da succeeded.
- Repo da co source Lambda va da cleanup cache artifacts.

## Follow-up: Google user chua co password

Sau khi test UI profile, phat hien Google-only user khong co mat khau hien tai nen khong the dung form doi mat khau cu.

Da sua tren branch `phuc-google-login`, push len `origin/phuc` voi commit:

- `bd1ec0a1 fix: allow Google users to set password`

Thay doi:

- Frontend luu them `authProvider` va `cognitoUsername` vao `auth_user` khi login native/Google.
- `SecurityTab` nhan dien Google user va doi flow tu `Doi mat khau` sang `Thiet lap mat khau`.
- Voi Google user, UI an field `Mat khau hien tai` vi tai khoan chua co native password.
- Request change password gui them `is_google_user` ve backend.
- Backend `ChangePasswordRequest.current_password` doi thanh optional.
- Backend `/api/profile/change-password` dung `extract_cognito_username_from_token()` de lay dung Cognito Username.
- `profile_service.change_password()` dung `current_username or email or user_id` khi goi `admin_set_user_password`.
- Native user van bi yeu cau nhap `current_password` nhu truoc.

Validation da chay cho follow-up nay:

```powershell
C:/msys64/ucrt64/bin/python.exe -m py_compile backend/app_api.py backend/modules/profile_service.py
npm run build
```

Ket qua:

- Python compile: pass.
- Frontend build: pass.
- Vite van co warning chunk JS > 500 kB, khong phai loi build.

### Follow-up bo sung: linked Google user van hien form native password

Sau khi test tiep, UI van hien `Mat khau hien tai` voi mot Google/linked user. Nguyen nhan co the la session `auth_user` cu chua co `authProvider`, hoac sau khi `AdminLinkProviderForUser` thanh cong Cognito tra `cognito:username` theo native username thay vi `Google_xxx`.

Da sua them voi commit:

- `e5785c23 fix: detect linked Google users from token claims`

Thay doi:

- Frontend `SecurityTab` doc ID token dang luu trong `sessionStorage`.
- Neu token co `cognito:username` bat dau bang `Google_`, hoac claim `identities` co `providerName/providerType = Google`, UI se coi la Google/linked user.
- Backend `/api/profile/change-password` cung decode token claims va tu suy luan Google identity tu `identities`, khong chi tin vao flag frontend.

Validation da chay lai:

```powershell
C:/msys64/ucrt64/bin/python.exe -m py_compile backend/app_api.py backend/modules/profile_service.py
npm run build
```

Ket qua: ca backend compile va frontend build deu pass.

## Follow-up: Cognito Hosted UI bao `Login pages unavailable`

Khi dang nhap Google, Cognito Hosted UI hien man hinh:

```text
Login pages unavailable
Please contact an administrator.
```

Nguyen nhan xac dinh:

- Frontend tao Google OAuth URL bang `window.location.origin`.
- Cognito app client ban dau chi co callback URL `http://localhost:5173/auth/callback`.
- Neu Vite dev server chay sang port khac nhu `5174`, `5175`, `5176`, redirect URI khong nam trong allowlist.
- Cognito tra ve `/error?error=redirect_mismatch&client_id=...`, hien thi thanh man `Login pages unavailable`.

Thao tac AWS da lam:

- Cap nhat app client `63f74h4dj78kqihhoimv4acl8a` trong user pool `us-east-1_3oq5wIiuu`.
- Them callback URLs local dev:
  - `http://localhost:5173/auth/callback`
  - `http://localhost:5174/auth/callback`
  - `http://localhost:5175/auth/callback`
  - `http://localhost:5176/auth/callback`
  - `http://127.0.0.1:5173/auth/callback`
  - `http://127.0.0.1:5174/auth/callback`
  - `http://127.0.0.1:5175/auth/callback`
  - `http://127.0.0.1:5176/auth/callback`
- Them logout URLs tuong ung cho `/login` tren cac origin tren.
- Giu OAuth flow `code`, scopes `openid email profile`, IdP `COGNITO` va `Google`.

Validation:

- Test authorize URL voi redirect URI `localhost:5173`, `5174`, `5175`, `5176`.
- Tat ca deu tra `302` sang `https://accounts.google.com/o/oauth2/v2/auth...`.
- Khong con redirect ve `/error?error=redirect_mismatch`.
