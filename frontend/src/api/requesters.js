import apiClient from "./client";

export async function getRequesters(params = {}) {
  const response = await apiClient.get("/requesters", { params });
  return response.data;
}

export async function getRequester(requesterId) {
  const response = await apiClient.get(`/requesters/${requesterId}`);
  return response.data;
}

export async function getMyRequesterProfile() {
  const response = await apiClient.get("/requesters/me");
  return response.data;
}

export async function updateMyRequesterProfile(data) {
  const response = await apiClient.patch("/requesters/me", data);
  return response.data;
}

export async function deleteRequester(requesterId) {
  await apiClient.delete(`/requesters/${requesterId}`);
}
