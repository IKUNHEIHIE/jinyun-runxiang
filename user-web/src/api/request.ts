import axios from 'axios'
import { ElMessage } from 'element-plus'
import { apiBase } from '../mobile/api'

const service = axios.create({
  baseURL: apiBase,
  timeout: 15000
})

// Only attach the current user's token; browsing never signs into a shared account.
service.interceptors.request.use(config => {
  const token = localStorage.getItem('jinyun_user_token')
  if (token && !config.url?.includes('/auth/login') && !config.url?.includes('/auth/register')) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 0) {
      ElMessage.error(res.message || '请求处理失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res.data
  },
  error => {
    if (error.response && error.response.status === 401) {
      ElMessage.warning('登录状态已失效，请重新登录')
      localStorage.removeItem('jinyun_user_token')
      localStorage.removeItem('jinyun_user_info')
      window.dispatchEvent(new Event('auth-required'))
    } else if (error.response && error.response.status === 403) {
      ElMessage.warning(error.response.data?.detail || '权限受限')
    } else {
      ElMessage.error(error.message || '网络连接异常')
    }
    return Promise.reject(error)
  }
)

export default service
