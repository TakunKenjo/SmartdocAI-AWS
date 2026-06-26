import axios from "axios"

const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 10000,
})

axiosClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // có thể xử lý lỗi chung ở đây
        return Promise.reject(error)
    }
)

export default axiosClient