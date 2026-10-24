import apiClient from "./client";

export async function getRequests(params = {}) {
  const response = await apiClient.get("/requests", { params });
  return response.data;
}

export async function getRequest(requestId) {
  const response = await apiClient.get(`/requests/${requestId}`);
  return response.data;
}

export async function createRequest(data) {
  const response = await apiClient.post("/requests", data);
  return response.data;
}

export async function deleteRequest(requestId) {
  await apiClient.delete(`/requests/${requestId}`);
}

export async function getRequestMatches(requestId) {
  const response = await apiClient.get(`/requests/${requestId}/matches`);
  return response.data;
}

export async function approveRequest(requestId) {
  const response = await apiClient.post(`/requests/${requestId}/approve`);
  return response.data;
}

export async function rejectRequest(requestId) {
  const response = await apiClient.post(`/requests/${requestId}/reject`);
  return response.data;
}

export async function issueRequest(requestId) {
  const response = await apiClient.post(`/requests/${requestId}/issue`);
  return response.data;
}
