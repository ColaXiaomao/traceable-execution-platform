import { defineStore } from "pinia";
import { ref } from "vue";
import { login, getMe } from "@/api/auth";
//Vue 组件之间不能直接共享数据，所以需要一个全局的地方来存这些信息，这就是 Pinia store

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const userInfo = ref<any>(null);

  async function loginByUsername(username: string, password: string) {
    const res = await login(username, password);
    token.value = res.data.access_token;
    localStorage.setItem("token", token.value);
    await fetchUserInfo();
  }

  async function fetchUserInfo() {
    const res = await getMe();
    userInfo.value = res.data;
  }

  function logout() {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
  }

  return { token, userInfo, loginByUsername, fetchUserInfo, logout };
});