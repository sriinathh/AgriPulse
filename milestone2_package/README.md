# Milestone 2 — Data Separation & Feature Engineering

This is a **separate mini-package** for your Smart Irrigation project role. It contains only the files needed for Milestone 2, not the full application.

## What this package does

1. Generates the project's irrigation training dataset using the existing `generate_dataset.py`.
2. Checks dataset columns, missing values and duplicate rows.
3. Creates a calendar feature called `month` from `date`.
4. Separates model inputs (`X`) from prediction targets (`y`).
5. Splits data by `field_id` into training and testing sets, so readings from one field do not appear in both sets.
6. Fills missing numeric/categorical input values and converts text categories into numeric columns.
7. Saves CSV outputs and a preprocessing object for the model-training teammate.

**Important:** The included irrigation dataset is SYNTHETIC / SIMULATED. It is not real farm measurement data. Mention this clearly in your report/presentation.

## Folder structure

```text
milestone2_package/
├── README.md
└── backend/
    ├── requirements-milestone2.txt
    ├── scripts/
    │   ├── generate_dataset.py
    │   └── prepare_milestone2.py
    └── data/
        ├── synthetic/
        │   └── irrigation_dataset.csv
        └── processed/
            └── milestone2/
                ├── X_train.csv
                ├── X_test.csv
                ├── y_train.csv
                ├── y_test.csv
                ├── train_fields.csv
                ├── test_fields.csv
                ├── preprocessor.joblib
                └── preparation_report.json
```

## How to run it on Windows

### 1. Extract the ZIP

Extract the ZIP file to a folder, for example:

`C:\Users\YourName\Downloads\milestone2_package`

### 2. Open the backend folder in VS Code

Open the extracted `backend` folder in VS Code. Then open Terminal. Confirm that the terminal path ends in `milestone2_package\backend`.

### 3. Install the Python libraries

If you already have your project virtual environment, activate it first. For example, if your full project has `.venv` in its root, activate that environment from the full project root before running the scripts.

Then run:

```powershell
python -m pip install -r requirements-milestone2.txt
```

Required packages: pandas, NumPy, scikit-learn and joblib. No separate external dataset download or API key is required.

### 4. Generate the irrigation dataset

Run from the `backend` folder:

```powershell
python scripts/generate_dataset.py
```

It creates `data/synthetic/irrigation_dataset.csv` (normally 2,808 rows with the default settings).

### 5. Run your Milestone 2 code

Still from the `backend` folder, run:

```powershell
python scripts/prepare_milestone2.py
```

If successful, the prepared files will be written to:

`backend\data\processed\milestone2\`

The ZIP already includes an example generated dataset and sample output files so you can inspect them. Running the commands recreates them.

## What each output file means

| File | Meaning |
|---|---|
| `X_train.csv` | Prepared input features used to train the model |
| `X_test.csv` | Prepared input features used to test the model |
| `y_train.csv` | Correct target answers for training: `irrigate_today`, `irrigation_mm` |
| `y_test.csv` | Correct target answers for testing |
| `train_fields.csv` | Field IDs allocated to training |
| `test_fields.csv` | Field IDs allocated to testing |
| `preprocessor.joblib` | Saved imputation/encoding rules; use this same object for future inputs |
| `preparation_report.json` | Summary of columns, row counts, split and quality checks |

## Simple explanation for your internship review

- **Data separation:** I separated input features from the two prediction targets, `irrigate_today` and `irrigation_mm`. Then I split the data into training and testing sets by field.
- **Feature engineering:** I derived `month` from the date and encoded text columns such as crop type, soil type, irrigation type and growth stage into numeric columns.
- **Data cleaning:** I checked missing values and duplicates, removed duplicate rows, and imputed missing input features.
- **Leakage prevention:** The field ID and date are not direct model inputs; target columns are excluded from inputs; preprocessing is fitted on training data only.
- **Limitation:** The data is simulated to test the pipeline. Model performance on this dataset does not prove performance on real farms.

## Important note for integrating into the full team project

This mini-package is standalone. If you want to merge it into the original project, copy `prepare_milestone2.py` into the original project's `backend/scripts/` folder. The original project's `generate_dataset.py` already exists, so do not overwrite it unless your team agrees. Run the script from the original `backend` folder. It expects the generated CSV at `backend/data/synthetic/irrigation_dataset.csv`.

The target values are simulation outputs, not verified real-world irrigation recommendations. Confirm the target definitions and expected columns with the teammate responsible for model training before final integration.
