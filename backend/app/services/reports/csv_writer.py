import csv
import io
from typing import Any, List


def generate_csv(columns: List[str], rows: List[List[Any]]) -> bytes:
    """Generate a clean UTF-8 CSV with column headers and rows."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")
