import client from "./client";

/**
 * Trigger shortage prediction pipeline execution.
 * @param {number} horizonDays - Forecast horizon between 7 and 30 days (default 30).
 */
export async function runPrediction(horizonDays = 30) {
  const response = await client.post("/predictions/run", {
    horizon_days: horizonDays,
  });
  return response.data;
}

/**
 * Fetch latest prediction run results and forecasts by blood group.
 */
export async function getLatestPredictions() {
  const response = await client.get("/predictions/latest");
  return response.data;
}

/**
 * Fetch shortage alerts for the latest prediction run within a given day window.
 * @param {number} withinDays - Detection window in days (7-30).
 */
export async function getPredictionAlerts(withinDays = 30) {
  const response = await client.get("/predictions/alerts", {
    params: { within_days: withinDays },
  });
  return response.data;
}

/**
 * Fetch latest model evaluation metrics (MAE, RMSE, selected model).
 */
export async function getPredictionEvaluation() {
  const response = await client.get("/predictions/evaluation");
  return response.data;
}

