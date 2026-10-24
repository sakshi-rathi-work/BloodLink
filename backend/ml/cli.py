import argparse
import os
import sys
from sqlalchemy import create_engine
from ml.config import DEFAULT_HORIZON_DAYS, get_default_safe_minimums
from ml.data import prepare_stock_series
from ml.evaluation import evaluate_and_select_models
from ml.pipeline import run_prediction


def get_db_engine():
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://bloodlink:bloodlink@localhost:5432/bloodlink")
    return create_engine(db_url)


def main():
    parser = argparse.ArgumentParser(description="BloodLink ML CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # evaluate sub-command
    subparsers.add_parser("evaluate", help="Build data, evaluate candidates, write evaluation JSON (no DB writes)")

    # run sub-command
    run_parser = subparsers.add_parser("run", help="Full prediction run: evaluate, forecast, persist to DB")
    run_parser.add_argument("--horizon", type=int, default=DEFAULT_HORIZON_DAYS, help="Horizon days (7-30)")

    args = parser.parse_args()
    engine = get_db_engine()
    safe_mins = get_default_safe_minimums()

    if args.command == "evaluate":
        print("Loading data from v_transactions...")
        group_data = prepare_stock_series(engine)
        print("Evaluating candidate models...")
        eval_dict, _ = evaluate_and_select_models(group_data)
        print("Evaluation complete. Results saved to artifacts/latest_evaluation.json.")
        print(f"Evaluated {len(eval_dict.get('groups', {}))} groups.")

    elif args.command == "run":
        horizon = max(7, min(30, args.horizon))
        print(f"Executing prediction pipeline with horizon={horizon} days...")
        res = run_prediction(engine, safe_minimums=safe_mins, horizon_days=horizon)
        print(f"Run completed successfully: run_id={res.run_id}")
        print(f"Groups predicted: {res.groups_predicted}, Groups skipped: {res.groups_skipped}")


if __name__ == "__main__":
    main()
