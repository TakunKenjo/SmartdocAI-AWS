// Kiểm tra ngưỡng alert (90%, 95% và 100%)
export const checkThresholdAlert = (oldValue, newValue, maxValue) => {
    // Nếu maxValue không hợp lệ (null, 0, âm) thì return -> tránh chia cho 0
    if (!maxValue || maxValue <= 0) return null;

    // chuyển gtri mới & cũ sang % so vs maxValue
    const oldPercent = (oldValue / maxValue) * 100;
    const newPercent = (newValue / maxValue) * 100;

    // Chỉ báo động nếu mốc phần trăm VƯỢT QUA các ngưỡng này (để tránh spam alert)
    /*  oldPercent < 100   → Trước khi thêm khoản chi: chưa vượt ngân sách
        newPercent >= 100  → Sau khi thêm khoản chi: đã vượt hoặc chạm 100%
        Ví dụ kích hoạt: 97% → 103% hoặc 99% → 100%
        Ví dụ KHÔNG kích hoạt: 100% → 110% (vì oldPercent < 100 là false — đã vượt từ trước rồi, không báo lại)
    */
    if (oldPercent < 100 && newPercent >= 100) return 100;
    /*
        oldPercent < 95              → Trước khi thêm: chưa chạm 95%
        newPercent >= 95             → Sau khi thêm: đã chạm hoặc vượt 95%
        newPercent < 100             → Nhưng chưa đến 100%: đảm bảo trường hợp nhảy thẳng từ 85% lên 102% sẽ không bị báo ngưỡng 95%, mà chỉ báo ngưỡng 100% (điều kiện 1 bắt trước rồi return)
    */
    if (oldPercent < 95 && newPercent >= 95 && newPercent < 100) return 95;
    /*
        oldPercent < 90              → Trước khi thêm: chưa chạm 90%
        newPercent >= 90             → Sau khi thêm: đã chạm hoặc vượt 90%
        newPercent < 95              → Nhưng chưa đến 95%: loại bỏ các trường hợp nhảy vọt qua 90% lên thẳng 95%+ (đã được điều kiện 1 hoặc 2 xử lý rồi).
    */
    if (oldPercent < 90 && newPercent >= 90 && newPercent < 95) return 90;

    return null; // Không chạm mốc nào mới
}