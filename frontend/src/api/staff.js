import apiClient from "./client";

export async function getStaff(params = {}) {
  const response = await apiClient.get("/staff", { params });
  return response.data;
}

export async function getStaffMember(staffId) {
  const response = await apiClient.get(`/staff/${staffId}`);
  return response.data;
}

export async function createStaff(data) {
  const response = await apiClient.post("/staff", data);
  return response.data;
}

export async function updateStaff(staffId, data) {
  const response = await apiClient.patch(`/staff/${staffId}`, data);
  return response.data;
}

export async function deleteStaff(staffId) {
  await apiClient.delete(`/staff/${staffId}`);
}
