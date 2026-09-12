import { http } from "@/utils/http";

const request = {
  get: <T = any>(url: string, params?: any): Promise<T> => {
    return http.request<any>("get", url, { params }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      return res;
    });
  },
  post: <T = any>(url: string, data?: any): Promise<T> => {
    return http.request<any>("post", url, { data }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      return res;
    });
  },
  put: <T = any>(url: string, data?: any): Promise<T> => {
    return http.request<any>("put", url, { data }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      return res;
    });
  },
  delete: <T = any>(url: string, params?: any): Promise<T> => {
    return http.request<any>("delete", url, { params }).then(res => {
      if (res && res.code === 0 && res.data !== undefined) return res.data;
      return res;
    });
  }
};

export default request;
