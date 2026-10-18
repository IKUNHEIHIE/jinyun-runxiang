import { http } from "@/utils/http";

const request = {
  get: <T = any>(url: string, params?: any): Promise<T> => {
    return http.request<any>("get", url, { params }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      throw new Error(res?.message || "请求失败");
    });
  },
  post: <T = any>(url: string, data?: any): Promise<T> => {
    return http.request<any>("post", url, { data }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      throw new Error(res?.message || "请求失败");
    });
  },
  put: <T = any>(url: string, data?: any): Promise<T> => {
    return http.request<any>("put", url, { data }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      throw new Error(res?.message || "请求失败");
    });
  },
  delete: <T = any>(url: string, params?: any): Promise<T> => {
    return http.request<any>("delete", url, { params }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      throw new Error(res?.message || "请求失败");
    });
  }
};

export default request;
