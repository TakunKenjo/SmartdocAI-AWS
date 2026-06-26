## Giải thích các kỹ thuật
<hr>

### 1. ```createSelector``` 
```createSelector``` là một "vũ khí hạng nặng" được tích hợp sẵn trong Redux Toolkit (thực chất nó đến từ thư viện reselect). Có thể hiểu nôm na: ```createSelector``` chính là ```useMemo``` nhưng dành riêng cho kho chứa (Store) của Redux.

#### 1.1. Cú pháp cơ bản của createSelector
Hàm này thường nhận vào 2 phần chính:
```js
import { createSelector } from '@reduxjs/toolkit';

export const myCustomSelector = createSelector(
  // Phần 1: Mảng các "Input Selectors" (Hàm lấy dữ liệu thô)
  [
    (state) => state.transactions.items, 
    (state) => state.categories.dictionary 
  ],
  
  // Phần 2: "Result Function" (Hàm xào nấu/xử lý dữ liệu)
  (transactions, categoryDict) => {
    // Thực hiện logic filter, map, sort... ở đây
    return /* Kết quả cuối cùng */;
  }
);
```
**Chi tiết:**
* **Phần 1 (Input Selectors):** Là một mảng chứa các hàm nhỏ. Nhiệm vụ của chúng chỉ đơn giản là đi vào state tổng của Redux và "nhặt" ra những mảnh dữ liệu thô cần thiết.
* **Phần 2 (Result Function):** Là hàm xử lý cuối cùng. Số lượng tham số của hàm này tương ứng đúng với số lượng Input Selectors ở Phần 1. Nghĩa là kết quả của Input 1 sẽ truyền vào tham số 1, kết quả Input 2 truyền vào tham số 2.

#### 1.2. Cách thức hoạt động: Phép thuật mang tên "Memoization" (Bộ nhớ đệm)
1. Lần chạy đầu tiên: Khi một component gọi useSelector(myCustomSelector), Redux sẽ chạy các Input Selectors để lấy dữ liệu thô, sau đó chạy Result Function để tính toán ra kết quả. ```createSelector``` sẽ âm thầm lưu lại kết quả này cùng với các giá trị đầu vào.
2. Các lần chạy sau (Khi State thay đổi): Giả sử người dùng vừa làm một hành động (Action) làm thay đổi state.user.name (không liên quan gì đến ```transactions``` hay `categories`).
   * Redux bắt buộc phải chạy lại các hàm selector.
   * ```createSelector``` sẽ chạy lại các Input Selectors. Nó lấy được ```transactions``` và ```categoryDict```.
   * **BƯỚC KIỂM TRA QUAN TRỌNG**: Nó mang 2 giá trị vừa lấy ra so sánh với 2 giá trị ở lần chạy trước bằng phép toán === (Reference Equality).
   * Vì ```transactions``` và ```categories``` không hề bị thay đổi, kết quả so sánh là true (giống y xì đúc).
   * **BỎ QUA TÍNH TOÁN**: ```createSelector``` sẽ không thèm chạy Result Function nữa (không map, không filter tốn CPU). Nó lập tức ném cái kết quả đã lưu trong bộ nhớ đệm ra cho Component.