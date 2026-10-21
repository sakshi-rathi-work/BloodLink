/**
 * Normalize and extract human-friendly error messages from API responses.
 * Supports both domain AppError envelopes {detail: {code, message}} and FastAPI 422 lists.
 */
export function getErrorMessage(error) {
  if (!error) return "An unexpected error occurred.";

  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;

    // Standard BloodLink domain error shape
    if (typeof detail === "object" && !Array.isArray(detail)) {
      if (detail.message) {
        if (detail.reasons && Array.isArray(detail.reasons)) {
          return `${detail.message} Reasons: ${detail.reasons.join(", ")}`;
        }
        return detail.message;
      }
      if (detail.code) {
        return `Error: ${detail.code}`;
      }
    }

    // FastAPI 422 validation error list
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          const field = item.loc ? item.loc.slice(1).join(".") : "Field";
          return `${field}: ${item.msg}`;
        })
        .join("; ");
    }

    if (typeof detail === "string") {
      return detail;
    }
  }

  if (error.message) {
    return error.message;
  }

  return "An unexpected server error occurred.";
}
