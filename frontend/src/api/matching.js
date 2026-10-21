import apiClient from "./client";

export async function getCompatibilityMatrix() {
  const response = await apiClient.get("/matching/compatibility");
  return response.data;
}

export async function findMatchingUnits(bloodGroup, limit = 50) {
  const response = await apiClient.get("/matching/units", {
    params: { blood_group: bloodGroup, limit },
  });
  return response.data;
}
