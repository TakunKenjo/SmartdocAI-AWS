import { CognitoUserPool } from "amazon-cognito-identity-js";

// Dùng sessionStorage thay vì mặc định (localStorage) để mỗi tab trình duyệt
// có 1 session Cognito độc lập. Nếu dùng localStorage (mặc định), đăng nhập
// user khác ở tab 2 sẽ ghi đè "LastAuthUser" và khiến tab 1 (đang hiển thị
// user A) vô tình gửi JWT của user B lên backend khi gọi API.
const poolData = {
  UserPoolId: "us-east-1_3oq5wIiuu",
  ClientId: "63f74h4dj78kqihhoimv4acl8a",
  Storage: window.sessionStorage,
};

export const userPool = new CognitoUserPool(poolData);

export const getSessionToken = () => {
  return new Promise((resolve) => {
    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      resolve(null);
      return;
    }
    cognitoUser.getSession((err, session) => {
      if (err) {
        resolve(null);
      } else {
        resolve(session.getIdToken().getJwtToken());
      }
    });
  });
};
