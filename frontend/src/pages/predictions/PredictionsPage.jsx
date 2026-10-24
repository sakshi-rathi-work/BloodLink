import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Play,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  getLatestPredictions,
  getPredictionAlerts,
  getPredictionEvaluation,
  runPrediction,
} from "../../api/predictions";
import ForecastChart from "../../components/charts/ForecastChart";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import EmptyState from "../../components/ui/EmptyState";
import ErrorBanner from "../../components/ui/ErrorBanner";
import Spinner from "../../components/ui/Spinner";

const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export default function PredictionsPage() {
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const [horizonDays, setHorizonDays] = useState(30);
  const [selectedGroup, setSelectedGroup] = useState("A+");

  const [latestData, setLatestData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [evalData, setEvalData] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [latestRes, alertsRes, evalRes] = await Promise.all([
        getLatestPredictions(),
        getPredictionAlerts(30),
        getPredictionEvaluation(),
      ]);
      setLatestData(latestRes);
      setAlerts(alertsRes || []);
      setEvalData(evalRes);

      // Select first group with predictions if current selected group is not in prediction list
      if (latestRes?.predictions?.length > 0) {
        const hasCurrent = latestRes.predictions.some(
          (p) => p.blood_group === selectedGroup
        );
        if (!hasCurrent) {
          setSelectedGroup(latestRes.predictions[0].blood_group);
        }
      }
    } catch (err) {
      setError(
        err.response?.data?.detail?.message ||
          err.message ||
          "Failed to load predictions data."
      );
    } finally {
      setLoading(false);
    }
  }, [selectedGroup]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunPrediction = async () => {
    setRunning(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await runPrediction(horizonDays);
      setSuccessMsg(
        `Prediction run completed successfully (${res.groups_predicted} groups forecast, ${res.groups_skipped?.length || 0} skipped).`
      );
      await loadData();
    } catch (err) {
      setError(
        err.response?.data?.detail?.message ||
          err.message ||
          "Failed to execute prediction run."
      );
    } finally {
      setRunning(false);
    }
  };

  const currentPrediction = latestData?.predictions?.find(
    (p) => p.blood_group === selectedGroup
  );

  const isCurrentSkipped = latestData?.skipped_groups?.some(
    (sg) => sg.blood_group === selectedGroup
  );
  const currentSkippedReason = latestData?.skipped_groups?.find(
    (sg) => sg.blood_group === selectedGroup
  )?.reason;

  const currentEval = evalData?.groups?.[selectedGroup];

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Shortage Predictions & Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Machine learning forecast models detecting projected blood unit shortages across 30 days.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm text-sm">
            <span className="text-slate-600 font-medium">Horizon:</span>
            <input
              type="number"
              min={7}
              max={30}
              value={horizonDays}
              onChange={(e) =>
                setHorizonDays(
                  Math.max(7, Math.min(30, parseInt(e.target.value) || 30))
                )
              }
              className="w-14 px-2 py-0.5 border border-slate-300 rounded text-center font-bold text-slate-800 focus:outline-none focus:ring-1 focus:ring-red-500"
            />
            <span className="text-slate-400">days</span>
          </div>

          <Button
            variant="danger"
            onClick={handleRunPrediction}
            disabled={running}
            icon={running ? Spinner : Play}
          >
            {running ? "Forecasting..." : "Run Prediction"}
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {successMsg && (
        <div className="flex items-center gap-2 bg-emerald-50 text-emerald-800 border border-emerald-200 px-4 py-3 rounded-lg text-sm font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : !latestData?.run_id ? (
        <EmptyState
          icon={TrendingUp}
          title="No Prediction Run Available"
          description="Click 'Run Prediction' above to generate blood shortage forecasts using historical donation and usage records."
          action={
            <Button
              variant="danger"
              onClick={handleRunPrediction}
              disabled={running}
            >
              Run First Prediction
            </Button>
          }
        />
      ) : (
        <>
          {/* Metadata banner */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 border border-slate-200 px-4 py-3 rounded-xl text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              <span>
                Last Run:{" "}
                <strong className="text-slate-800">
                  {latestData.generated_at
                    ? new Date(latestData.generated_at).toLocaleString()
                    : "—"}
                </strong>
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span>
                Run ID: <code className="font-mono text-slate-700">{latestData.run_id?.slice(0, 8)}...</code>
              </span>
              <span>
                Groups Active:{" "}
                <strong className="text-emerald-700">
                  {latestData.predictions?.length || 0} / {BLOOD_GROUPS.length}
                </strong>
              </span>
            </div>
          </div>

          {/* Shortage Alerts Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Active Shortage Alerts ({alerts.length})
              </h2>
              <span className="text-xs text-slate-500">
                Projected to breach safe threshold within 30 days
              </span>
            </div>

            {alerts.length === 0 ? (
              <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-200 p-4 rounded-xl text-sm text-emerald-800">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                <div>
                  <p className="font-semibold">All Blood Groups Within Safe Stock</p>
                  <p className="text-xs text-emerald-600 mt-0.5">
                    No shortages projected across the configured forecasting window.
                  </p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {alerts.map((alert) => (
                  <div
                    key={alert.blood_group}
                    className="bg-white border-2 border-red-200 p-4 rounded-xl shadow-sm hover:border-red-300 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xl font-extrabold text-red-600">
                        {alert.blood_group}
                      </span>
                      <Badge variant="emergency">
                        {alert.days_until_shortage === 0
                          ? "Shortage Today"
                          : `in ${alert.days_until_shortage} days`}
                      </Badge>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-600 mt-3">
                      <div className="flex justify-between">
                        <span>Current Available:</span>
                        <strong className="text-slate-800">{alert.current_stock} units</strong>
                      </div>
                      <div className="flex justify-between">
                        <span>Safe Minimum:</span>
                        <strong className="text-slate-800">{alert.safe_minimum} units</strong>
                      </div>
                      <div className="flex justify-between">
                        <span>First Shortage Date:</span>
                        <strong className="text-red-700">{alert.first_shortage_date}</strong>
                      </div>
                      <div className="flex justify-between">
                        <span>Lowest Predicted:</span>
                        <strong className="text-red-600">{alert.min_predicted_stock} units</strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Blood Group Tabs & Detailed Forecast */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900 mb-3">
                Blood Group Forecast Detail
              </h2>

              {/* Tabs */}
              <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
                {BLOOD_GROUPS.map((bg) => {
                  const isSelected = selectedGroup === bg;
                  const hasAlert = alerts.some((a) => a.blood_group === bg);
                  const isSkipped = latestData.skipped_groups?.some(
                    (sg) => sg.blood_group === bg
                  );

                  return (
                    <button
                      key={bg}
                      type="button"
                      onClick={() => setSelectedGroup(bg)}
                      className={`px-4 py-2 rounded-lg font-bold text-sm transition-all flex items-center gap-1.5 ${
                        isSelected
                          ? "bg-slate-900 text-white shadow-sm"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      <span>{bg}</span>
                      {hasAlert && (
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                      )}
                      {isSkipped && (
                        <span className="text-[10px] text-amber-500 uppercase font-semibold">
                          (Skipped)
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tab content */}
            {isCurrentSkipped ? (
              <div className="p-8 text-center bg-amber-50 rounded-xl border border-amber-200">
                <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                <h3 className="text-base font-bold text-amber-900">
                  Blood Group {selectedGroup} Skipped
                </h3>
                <p className="text-sm text-amber-700 mt-1">
                  Reason: <code className="font-mono font-semibold">{currentSkippedReason || "insufficient_data"}</code>.
                  This group requires at least 90 days of recorded operational transactions to evaluate forecasting models.
                </p>
              </div>
            ) : currentPrediction ? (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-extrabold text-slate-900">
                      {selectedGroup}
                    </span>
                    <Badge variant="info">
                      Model: {currentPrediction.model_name.replace("_", " ").toUpperCase()}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      Safe Minimum: <strong>{currentPrediction.safe_minimum} units</strong>
                    </span>
                  </div>
                </div>

                <ForecastChart
                  forecast={currentPrediction.forecast}
                  safeMinimum={currentPrediction.safe_minimum}
                  bloodGroup={selectedGroup}
                />
              </div>
            ) : (
              <div className="p-8 text-center text-sm text-slate-500">
                No prediction found for {selectedGroup}.
              </div>
            )}

            {/* Model Evaluation & Accuracy Table */}
            {currentEval?.metrics && (
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <TrendingDown className="w-4 h-4 text-blue-600" />
                    Model Performance Comparison on Hold-out Data ({evalData?.holdout_days || 30} Days)
                  </h3>
                  <span className="text-xs text-slate-500">
                    Training History: <strong>{currentEval.train_days || "—"} days</strong>
                  </span>
                </div>

                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 uppercase font-semibold">
                      <tr>
                        <th className="px-4 py-2.5">Candidate Model</th>
                        <th className="px-4 py-2.5">Status</th>
                        <th className="px-4 py-2.5">MAE (Mean Absolute Error)</th>
                        <th className="px-4 py-2.5">RMSE (Root Mean Square Error)</th>
                        <th className="px-4 py-2.5">Selection</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {Object.entries(currentEval.metrics).map(([mName, mVals]) => {
                        const isWinner = currentEval.selected_model === mName;
                        return (
                          <tr
                            key={mName}
                            className={
                              isWinner
                                ? "bg-blue-50/60 font-semibold text-blue-900"
                                : "text-slate-700"
                            }
                          >
                            <td className="px-4 py-2.5 capitalize">
                              {mName.replace("_", " ")}
                            </td>
                            <td className="px-4 py-2.5">
                              {mVals.error ? (
                                <span className="text-red-600 font-normal">Failed</span>
                              ) : (
                                <span className="text-emerald-700">Fitted</span>
                              )}
                            </td>
                            <td className="px-4 py-2.5">
                              {mVals.mae !== undefined ? `${mVals.mae} units` : "—"}
                            </td>
                            <td className="px-4 py-2.5">
                              {mVals.rmse !== undefined ? `${mVals.rmse} units` : "—"}
                            </td>
                            <td className="px-4 py-2.5">
                              {isWinner ? (
                                <Badge variant="info">Selected (Lowest RMSE)</Badge>
                              ) : (
                                <span className="text-slate-400">—</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
