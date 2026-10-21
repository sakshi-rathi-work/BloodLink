import apiClient from "./client";

export async function getDonors(params = {}) {
  const response = await apiClient.get("/donors", { params });
  return response.data;
}

export async function getDonor(donorId) {
  const response = await apiClient.get(`/donors/${donorId}`);
  return response.data;
}

export async function createDonor(data) {
  const response = await apiClient.post("/donors", data);
  return response.data;
}

export async function updateDonor(donorId, data) {
  const response = await apiClient.patch(`/donors/${donorId}`, data);
  return response.data;
}

export async function deleteDonor(donorId) {
  const response = await apiClient.delete(`/donors/${donorId}`);
  return response.data;
}

export async function getDonorEligibility(donorId) {
  const response = await apiClient.get(`/donors/${donorId}/eligibility`);
  return response.data;
}

export async function recordDonation(donorId) {
  const response = await apiClient.post(`/donors/${donorId}/donations`);
  return response.data;
}

export async function getDonationHistory(donorId) {
  const response = await apiClient.get(`/donors/${donorId}/donations`);
  return response.data;
}
