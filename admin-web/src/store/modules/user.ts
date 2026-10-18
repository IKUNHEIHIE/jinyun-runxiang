import { defineStore } from "pinia";
import {
  type userType,
  store,
  router,
  resetRouter,
  routerArrays,
  storageLocal
} from "../utils";
import {
  type UserResult,
  type RefreshTokenResult,
  getLogin,
  refreshTokenApi,
  getLoginLogout
} from "@/api/user";
import { useMultiTagsStoreHook } from "./multiTags";
import { type DataInfo, setToken, removeToken, userKey } from "@/utils/auth";

export const useUserStore = defineStore("pure-user", {
  state: (): userType => ({
    // 头像
    avatar: storageLocal().getItem<DataInfo<number>>(userKey)?.avatar ?? "",
    // 用户名
    username: storageLocal().getItem<DataInfo<number>>(userKey)?.username ?? "",
    // 昵称
    nickname: storageLocal().getItem<DataInfo<number>>(userKey)?.nickname ?? "",
    // 页面级别权限
    roles: storageLocal().getItem<DataInfo<number>>(userKey)?.roles ?? [],
    // 按钮级别权限
    permissions:
      storageLocal().getItem<DataInfo<number>>(userKey)?.permissions ?? [],
    // 是否勾选了登录页的免登录
    isRemembered: false,
    // 登录页的免登录存储几天，默认7天
    loginDay: 7
  }),
  actions: {
    /** 存储头像 */
    SET_AVATAR(avatar: string) {
      this.avatar = avatar;
    },
    /** 存储用户名 */
    SET_USERNAME(username: string) {
      this.username = username;
    },
    /** 存储昵称 */
    SET_NICKNAME(nickname: string) {
      this.nickname = nickname;
    },
    /** 存储角色 */
    SET_ROLES(roles: Array<string>) {
      this.roles = roles;
    },
    /** 存储按钮级别权限 */
    SET_PERMS(permissions: Array<string>) {
      this.permissions = permissions;
    },
    /** 存储是否勾选了登录页的免登录 */
    SET_ISREMEMBERED(bool: boolean) {
      this.isRemembered = bool;
    },
    /** 设置登录页的免登录存储几天 */
    SET_LOGINDAY(value: number) {
      this.loginDay = Number(value);
    },
    /** 登入 */
    async loginByUsername(data) {
      return new Promise<any>((resolve, reject) => {
        getLogin(data)
          .then((res: any) => {
            if (res?.code === 0 && res?.data) {
              const u = res.data.user || {};
              if (!["ADMIN", "TEACHER"].includes(u.role_code)) {
                reject(new Error("此账号没有管理后台权限"));
                return;
              }
              const tokenData: any = {
                accessToken: res.data.token,
                refreshToken: res.data.token,
                expires: new Date(Date.now() + 86400000 * 7),
                username: u.username || (data as any)?.username,
                nickname: u.nickname || "系统超级管理员",
                avatar: u.avatar_url || "/static/images/default_avatar.svg",
                roles: [u.role_code || "admin"],
                permissions:
                  u.role_code === "ADMIN" ? ["*:*:*"] : ["teacher:workspace"]
              };
              setToken(tokenData);
              this.SET_USERNAME(tokenData.username);
              this.SET_NICKNAME(tokenData.nickname);
              this.SET_AVATAR(tokenData.avatar);
              this.SET_ROLES(tokenData.roles);
              this.SET_PERMS(tokenData.permissions);
              resolve({ success: true, data: tokenData });
            } else {
              reject(new Error(res?.message || "登录失败"));
            }
          })
          .catch(error => {
            reject(error);
          });
      });
    },
    /** 前端登出（不调用接口） */
    async logOut() {
      try {
        await getLoginLogout();
      } catch {
        /* Clear local state even when already expired. */
      }
      this.username = "";
      this.roles = [];
      this.permissions = [];
      removeToken();
      useMultiTagsStoreHook().handleTags("equal", [...routerArrays]);
      resetRouter();
      router.push("/login");
    },
    /** 刷新`token` */
    async handRefreshToken(data) {
      return new Promise<RefreshTokenResult>((resolve, reject) => {
        refreshTokenApi(data)
          .then(data => {
            if (data) {
              setToken(data.data);
              resolve(data);
            }
          })
          .catch(error => {
            reject(error);
          });
      });
    }
  }
});

export function useUserStoreHook() {
  return useUserStore(store);
}
