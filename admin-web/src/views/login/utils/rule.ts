import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** Login accepts existing passwords; password creation policy belongs to registration. */
export const REGEXP_PWD = /^[\s\S]{1,128}$/;

/** 登录校验 */
const loginRules = reactive<FormRules>({
  password: [
    {
      validator: (rule, value, callback) => {
        if (value === "") {
          callback(new Error("请输入密码"));
        } else if (!REGEXP_PWD.test(value)) {
          callback(
            new Error("密码长度不能超过128位")
          );
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
});

export { loginRules };
