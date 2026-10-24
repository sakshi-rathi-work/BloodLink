import apiClient from "./client";

export async function getCamps(params = {}) {
  const response = await apiClient.get("/camps", { params });
  return response.data;
}

export async function getCamp(campId) {
  const response = await apiClient.get(`/camps/${campId}`);
  return response.data;
}

export async function createCamp(data) {
  const response = await apiClient.post("/camps", data);
  return response.data;
}

export async function updateCamp(campId, data) {
  const response = await apiClient.patch(`/camps/${campId}`, data);
  return response.data;
}

export async function deleteCamp(campId) {
  await apiClient.delete(`/camps/${campId}`);
}
