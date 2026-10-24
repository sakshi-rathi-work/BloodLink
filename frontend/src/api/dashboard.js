import apiClient from "./client";

export async function getDashboardSummary() {
  const response = await apiClient.get("/dashboard/summary");
  return response.data;
}

export async function getDashboardTrends(params = {}) {
  const response = await apiClient.get("/dashboard/trends", { params });
  return response.data;
}

export async function getDashboardWastage(params = {}) {
  const response = await apiClient.get("/dashboard/wastage", { params });
  return response.data;
}
