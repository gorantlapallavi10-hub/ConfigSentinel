import api from "./client";

export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await api.post("/api/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  localStorage.setItem("cs_token", res.data.access_token);
  return res.data;
}

export async function register(username, password) {
  const res = await api.post("/api/auth/register", { username, password });
  localStorage.setItem("cs_token", res.data.access_token);
  return res.data;
}

export function logout() {
  localStorage.removeItem("cs_token");
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem("cs_token"));
}
