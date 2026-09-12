import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// 请求拦截器注入 Token (若无则自动获取管理员开发Token)
service.interceptors.request.use(
  async config => {
    let token = localStorage.getItem('jinyun_admin_token')
    if (!token && !config.url?.includes('/auth/login')) {
      try {
        const authRes = await axios.post('/api/auth/login', {
          username: 'admin',
          password: 'admin123'
        })
        if (authRes.data && authRes.data.code === 0) {
          token = authRes.data.data.token
          localStorage.setItem('jinyun_admin_token', token as string)
        }
      } catch (e) {
        console.warn('Auto auth skipped', e)
      }
    }
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

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
      localStorage.removeItem('jinyun_admin_token')
    } else {
      ElMessage.error(error.message || '网络连接异常')
    }
    return Promise.reject(error)
  }
)

export default service
