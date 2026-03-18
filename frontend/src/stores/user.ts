import { defineStore } from "pinia";
import { ref } from "vue";
import { login, getMe } from "@/api/auth";
import type { User } from "@/types/user";

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const userInfo = ref<User | null>(
    JSON.parse(localStorage.getItem("userInfo") || "null")
  );

  async function loginByUsername(username: string, password: string) {
    const res = await login(username, password);
    token.value = res.data.access_token;
    localStorage.setItem("token", token.value);
    await fetchUserInfo();
  }

  async function fetchUserInfo() {
    const res = await getMe();
    userInfo.value = res.data;
    localStorage.setItem("userInfo", JSON.stringify(res.data));
  }

  function logout() {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("userInfo");
  }

  return { token, userInfo, loginByUsername, fetchUserInfo, logout };
});