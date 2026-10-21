import apiClient from "./client";

export async function getStock() {
  const response = await apiClient.get("/inventory/stock");
  return response.data;
}

export async function getUnits(params = {}) {
  const response = await apiClient.get("/inventory/units", { params });
  return response.data;
}

export async function getUnit(unitId) {
  const response = await apiClient.get(`/inventory/units/${unitId}`);
  return response.data;
}

export async function getExpiringUnits(days = 7) {
  const response = await apiClient.get("/inventory/expiring", {
    params: { days },
  });
  return response.data;
}

export async function runExpirySweep() {
  const response = await apiClient.post("/inventory/expire-overdue");
  return response.data;
}

export async function deleteUnit(unitId) {
  const response = await apiClient.delete(`/inventory/units/${unitId}`);
  return response.data;
}
