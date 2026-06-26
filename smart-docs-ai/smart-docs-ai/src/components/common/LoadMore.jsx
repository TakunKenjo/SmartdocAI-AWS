const LoadMore = ({ loadMoreRef }) => {
    return (
        <div
            ref={loadMoreRef}
            className="py-6 text-center text-sm text-emerald-600 dark:text-emerald-400 animate-pulse font-medium"
        >
            <i className="fa-solid fa-spinner fa-spin mr-2"></i> Đang tải thêm...
        </div>
    )
}
export default LoadMore
