import request from "@/utils/request";
import type { User } from "@/types/user";

export const login = (username: string, password: string) =>
  request.post<{ access_token: string; token_type: string }>("/auth/login", { username, password });

export const getMe = () => request.get<User>("/auth/me");