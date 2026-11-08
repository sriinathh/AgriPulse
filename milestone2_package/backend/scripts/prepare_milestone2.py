"""
Milestone 2: Data Separation and Feature Engineering
Input: backend/data/synthetic/irrigation_dataset.csv
Output: backend/data/processed/milestone2/
Note: Input dataset is simulated by generate_dataset.py, not real farm measurements.
"""
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "synthetic" / "irrigation_dataset.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "milestone2"
TARGET_COLUMNS = ["irrigate_today", "irrigation_mm"]
GROUP_COLUMN = "field_id"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}\n"
            "First run: python scripts/generate_dataset.py\n"
            "Run that command from the backend folder."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_FILE)

    print("=" * 60)
    print("MILESTONE 2: DATA SEPARATION AND FEATURE ENGINEERING")
    print("=" * 60)
    print(f"Input file: {INPUT_FILE}")
    print(f"Original shape: {df.shape}")
    print("\nColumns:")
    print(", ".join(df.columns))

    # 1) Basic quality checks
    missing_before = df.isna().sum().to_dict()
    duplicates_before = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    required = [GROUP_COLUMN, "date", *TARGET_COLUMNS]
    missing_required = [col for col in required if col not in df.columns]
    if missing_required:
        raise ValueError(f"Required columns missing from dataset: {missing_required}")

    # Rows without target values cannot be used for supervised training.
    df = df.dropna(subset=TARGET_COLUMNS + [GROUP_COLUMN, "date"]).copy()

    # 2) Feature engineering: derive month from date.
    # Keep date out of the model input to avoid treating the full date as a category.
    parsed_date = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = int(parsed_date.isna().sum())
    df = df.loc[parsed_date.notna()].copy()
    df["month"] = parsed_date.loc[parsed_date.notna()].dt.month.astype(int)

    # 3) Separate model inputs (X), prediction targets (y), and field groups.
    # field_id is retained only for group-aware splitting, not used as a model feature.
    # Target columns must never be included in X (target leakage).
    excluded = [GROUP_COLUMN, "date", *TARGET_COLUMNS]
    X = df.drop(columns=excluded, errors="ignore").copy()
    y = df[TARGET_COLUMNS].copy()
    groups = df[GROUP_COLUMN].copy()

    if X.empty:
        raise ValueError("No input features remain after excluding IDs, date, and targets.")

    # 4) Split by field, not by individual row, so the same field cannot be
    # present in both train and test sets.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
    y_train, y_test = y.iloc[train_idx].copy(), y.iloc[test_idx].copy()
    train_groups = groups.iloc[train_idx]
    test_groups = groups.iloc[test_idx]

    # 5) Fit imputers/encoder only on training data to avoid data leakage.
    numeric_cols = X_train.select_dtypes(include="number").columns.tolist()
    categorical_cols = X_train.select_dtypes(exclude="number").columns.tolist()

    transformers = []
    if numeric_cols:
        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
        ])
        transformers.append(("numeric", numeric_pipeline, numeric_cols))

    if categorical_cols:
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        transformers.append(("categorical", categorical_pipeline, categorical_cols))

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")

    X_train_array = preprocessor.fit_transform(X_train)
    X_test_array = preprocessor.transform(X_test)
    feature_names = preprocessor.get_feature_names_out()

    X_train_processed = pd.DataFrame(
        X_train_array, columns=feature_names, index=X_train.index
    )
    X_test_processed = pd.DataFrame(
        X_test_array, columns=feature_names, index=X_test.index
    )

    # 6) Save outputs for the model-training teammate.
    X_train_processed.to_csv(OUTPUT_DIR / "X_train.csv", index=False)
    X_test_processed.to_csv(OUTPUT_DIR / "X_test.csv", index=False)
    y_train.to_csv(OUTPUT_DIR / "y_train.csv", index=False)
    y_test.to_csv(OUTPUT_DIR / "y_test.csv", index=False)

    # Keep field IDs separate for checking that train/test fields do not overlap.
    pd.DataFrame({"field_id": sorted(train_groups.unique())}).to_csv(
        OUTPUT_DIR / "train_fields.csv", index=False
    )
    pd.DataFrame({"field_id": sorted(test_groups.unique())}).to_csv(
        OUTPUT_DIR / "test_fields.csv", index=False
    )

    joblib.dump(preprocessor, OUTPUT_DIR / "preprocessor.joblib")

    report = {
        "input_file": str(INPUT_FILE),
        "dataset_type": "synthetic / simulated, not real farm measurements",
        "original_rows": int(len(pd.read_csv(INPUT_FILE))),
        "rows_after_deduplication_and_target_check": int(len(df)),
        "original_columns": list(pd.read_csv(INPUT_FILE).columns),
        "feature_columns_before_encoding": list(X.columns),
        "target_columns": TARGET_COLUMNS,
        "numeric_feature_columns": numeric_cols,
        "categorical_feature_columns": categorical_cols,
        "missing_values_before_cleaning": {k: int(v) for k, v in missing_before.items()},
        "duplicate_rows_found_before_cleaning": duplicates_before,
        "invalid_dates_removed": invalid_dates,
        "train_rows": int(len(X_train_processed)),
        "test_rows": int(len(X_test_processed)),
        "train_fields": sorted(str(x) for x in train_groups.unique()),
        "test_fields": sorted(str(x) for x in test_groups.unique()),
        "processed_feature_names": list(feature_names),
        "notes": [
            "field_id and date are not model input features.",
            "irrigate_today and irrigation_mm are target columns and are excluded from X.",
            "Preprocessing is fitted only on training data, then applied to test data.",
            "Rows from the same field are kept in either train or test, never both."
        ],
    }
    with open(OUTPUT_DIR / "preparation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Verify field separation.
    overlap = set(train_groups.unique()) & set(test_groups.unique())
    if overlap:
        raise RuntimeError(f"Data leakage: fields occur in both sets: {sorted(overlap)}")

    print("\nCompleted successfully!")
    print(f"Training rows: {len(X_train_processed)}")
    print(f"Testing rows: {len(X_test_processed)}")
    print(f"Input features before encoding: {len(X.columns)}")
    print(f"Features after encoding: {len(feature_names)}")
    print(f"Training fields: {len(train_groups.unique())}")
    print(f"Testing fields: {len(test_groups.unique())}")
    print(f"Output folder: {OUTPUT_DIR}")
    print("\nCreated files:")
    for path in sorted(OUTPUT_DIR.iterdir()):
        print(f" - {path.name}")


if __name__ == "__main__":
    main()
