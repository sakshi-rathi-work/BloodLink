import apiClient from "./client";

export async function getActivityLogs(params = {}) {
  const response = await apiClient.get("/activity-logs", { params });
  return response.data;
}
