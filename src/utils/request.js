import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import router from "@/router";

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})

// 请求拦截器
request.interceptors.request.use((config) => {
    const authStore = useAuthStore()
    
    console.log('请求配置:', {
        url: config.url,
        baseURL: config.baseURL,
        fullURL: config.baseURL + config.url,
        method: config.method,
        headers: config.headers,
        data: config.data,
        dataType: config.data instanceof FormData ? 'FormData' : typeof config.data
    });
    if (config.data instanceof FormData) {
        delete config.headers['Content-Type'];
    } else {
        // 对于JSON数据，添加Content-Type
        config.headers['Content-Type'] = 'application/json';
    }

    // 确保在请求时获取最新的token
    const token = authStore.token || localStorage.getItem('jwt')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
}, (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error)
})

// 响应拦截器
request.interceptors.response.use((response) => {
    console.log('响应成功:', {
        url: response.config.url,
        status: response.status,
        data: response.data
    });
    return response
}, async (error) => {
    console.error('响应错误详情:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        config: error.config
    });

    const authStore = useAuthStore()
    
    if(error.response?.status === 401) {
        console.log('401未授权，清除token并跳转登录');
        // 清除无效token
        authStore.logout()
        
        // 获取当前路由
        const currentRoute = router.currentRoute.value;
        
        // 避免无限重定向
        if (currentRoute.path !== '/login') {
            router.push({
                path: '/login',
                query: { redirect: currentRoute.fullPath }
            });
        }
    } else if (error.response?.status === 404) {
        console.error('API接口未找到，请检查后端路由');
    } else if (error.response?.status >= 500) {
        console.error('服务器内部错误，请检查后端日志');
    }
    
    return Promise.reject(error);
})

// 添加取消请求支持
request.CancelToken = axios.CancelToken
request.isCancel = axios.isCancel

export default request;