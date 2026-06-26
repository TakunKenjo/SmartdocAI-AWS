// Tạo 1 bảng tra cứu category theo id
export const buildCategoryById = (categories = []) =>
    // Mỗi category c được chuyển thành một cặp dạng [key, value]
    // key: id của category
    // value: cả object category c
    // --> tra cứu category theo id bằng .get()
    // Dùng Map thì vì .find() vì:
    // - find() phải quét mảng từ đầu đến cuối: O(n) mỗi lần tìm.
    // - Map.get() là tra cứu trực tiếp: gần như O(1).
    new Map(categories.map((c) => [String(c.id), c]))

// tạo ra một mảng objects “đã được ghép thêm dữ liệu category”
// ban đầu 1 object chỉ lưu thuộc tính categoryId
// hàm này ghép thêm object category tương ứng (lấy bằng gtri categoryId của object) vào object đó
export const withCategory = (dataArr = [], categoryById) =>
    // Duyệt từng budget b trong mảng budgets.
    // Trả về một object mới cho mỗi budget (không mutate object cũ).
    dataArr.map((b) => ({
        ...b, // spread operator: Copy toàn bộ field của budget hiện tại sang object mới.
        category: categoryById.get(String(b.categoryId)), // lấy ra category tương ứng với budget đó
    }));

export const formatDateToVNDate = (dateStr) => {
    const date = new Date(dateStr);

    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();

    return `${day}/${month}/${year}`;
};

export const calculatePercent = (current, total) => {
    if (!total || total <= 0) return 0;
    return (current / total) * 100;
}