#### `common/`
- **Mục đích**: Components cơ bản, không phụ thuộc vào business logic
- **Nội dung**: Button, Input, Modal, Loading, ErrorBoundary
- **Ví dụ**:
```jsx
// Button.jsx - Wrapper component sử dụng Shadcn
import { Button as ShadcnButton } from '@/components/ui/button';

export const Button = ({ variant = 'default', ...props }) => {
  return <ShadcnButton variant={variant} {...props} />;
};
```