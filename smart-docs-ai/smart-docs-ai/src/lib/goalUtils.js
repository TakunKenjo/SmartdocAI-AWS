export const getDaysLeft = (targetDateStr) => {
    const targetDate = new Date(targetDateStr);
    const today = new Date();

    targetDate.setHours(0,0,0,0);
    today.setHours(0,0,0,0);

    const diffTime = targetDate - today;

    // chuyển khoảng thời gian từ milliseconds → số ngày và làm tròn lên
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

