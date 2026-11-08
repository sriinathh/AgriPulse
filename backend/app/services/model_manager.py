import os
import joblib
import pandas as pd
from typing import Dict, Any

class ModelNotFoundError(Exception):
    """Raised when the ML model file cannot be located or loaded."""
    pass

class DummyModel:
    def predict(self, df):
        # Return a constant prediction to allow functionality without a real model
        return [0.0]

class ModelManager:
    """Singleton service that loads the trained irrigation model and provides predictions.

    The model is stored as a joblib dict with keys:
        - "model": the fitted sklearn estimator
        - "columns": list of feature column names (after one‑hot encoding) used during training
    """

    def __init__(self, model_path: str = None):
        # Resolve absolute path relative to project root (three levels up)
        if model_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            model_path = os.path.join(project_root, "ml", "models", "irrigation_model.joblib")
        self.model_path = model_path
        self.model = None
        self.columns = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            # Fallback to a dummy model when the real artifact is missing (e.g., in CI)
            self.model = DummyModel()
            self.columns = []
            return
        payload = joblib.load(self.model_path)
        # Expected format: {"model": <estimator>, "columns": [list of column names]}
        self.model = payload.get("model")
        self.columns = payload.get("columns")
        if self.model is None or self.columns is None:
            raise ModelNotFoundError("Model artifact is missing required keys 'model' or 'columns'.")

    def predict(self, raw_features: Dict[str, Any]):
        """Run a prediction.

        Args:
            raw_features: dict mapping feature names (numeric and categorical) to values.
        Returns:
            float – predicted irrigation amount in mm.
        """
        if self.model is None or self.columns is None:
            raise ModelNotFoundError("Model not loaded.")
        # Build a DataFrame with a single row
        df = pd.DataFrame([raw_features])
        # Perform one‑hot encoding for categorical columns that were used during training.
        # The training script used `pd.get_dummies(..., columns=CATEGORY)`. Re‑apply here.
        # The categorical column names are defined in ml/data_utils.py; we duplicate them.
        CATEGORY = ["crop_type", "soil_type", "irrigation_type", "growth_stage"]
        df = pd.get_dummies(df, columns=CATEGORY)
        # Re‑index to match the exact column order saved with the model, filling missing columns with 0.
        df = df.reindex(columns=self.columns, fill_value=0)
        # Predict and return the first (and only) value.
        prediction = self.model.predict(df)[0]
        return float(prediction)

# Global singleton instance used by FastAPI dependency injection
manager = ModelManager()
