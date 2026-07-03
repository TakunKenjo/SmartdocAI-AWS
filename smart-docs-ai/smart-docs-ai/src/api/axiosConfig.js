import axios from "axios"

const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 300000,
})

axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const config = error.config;
        if (!config) return Promise.reject(error);

        // Tự động thử lại ngầm khi gặp 503/504 (Server Cold Start hoặc đang xử lý tác vụ dài)
        const isRetryableError =
            error.response?.status === 503 ||
            error.response?.status === 504 ||
            error.code === 'ECONNABORTED' ||
            !error.response;

        if (isRetryableError) {
            config.__retryCount = config.__retryCount || 0;
            const maxRetries = config.maxRetries ?? 10;
            const retryDelay = config.retryDelay ?? 5000;

            if (config.__retryCount < maxRetries) {
                config.__retryCount += 1;
                console.info(`[SmartDocAI] Server đang phản hồi (Lần thử ${config.__retryCount}/${maxRetries})...`);
                await new Promise((resolve) => setTimeout(resolve, retryDelay));
                return axiosClient(config);
            }
        }

        return Promise.reject(error);
    }
)

export default axiosClient
