from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CropRecommendationRequest(BaseModel):
    N: float = Field(..., ge=0.0, le=200.0, description="Nitrogen ratio in soil (kg/ha)")
    P: float = Field(..., ge=0.0, le=200.0, description="Phosphorus ratio in soil (kg/ha)")
    K: float = Field(..., ge=0.0, le=250.0, description="Potassium ratio in soil (kg/ha)")
    temperature: float = Field(..., ge=-10.0, le=60.0, description="Ambient temperature (°C)")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity (%)")
    ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH level (0-14)")
    rainfall: float = Field(..., ge=0.0, le=500.0, description="Rainfall (mm)")
    soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0, description="Optional soil moisture (%)")


class CropCandidate(BaseModel):
    crop: str
    probability: float
    confidence_pct: float


class CropRecommendationResponse(BaseModel):
    recommended_crop: str
    confidence: float
    top_candidates: List[CropCandidate]
    agronomic_explanation: str
    input_parameters: Dict[str, float]
    model_metadata: Dict[str, Any]
    limitations: str


class CropModelMetricsResponse(BaseModel):
    model_name: str
    algorithm: str
    train_samples: int
    test_samples: int
    test_accuracy: float
    macro_f1: float
    feature_names: List[str]
    feature_importances: Dict[str, float]
    trained_at: str
    notes: List[str]


class IrrigationRecommendationRequest(BaseModel):
    field_id: Optional[str] = None
    crop_type: Optional[str] = None
    growth_stage: Optional[str] = Field("vegetative", description="seedling, vegetative, flowering, maturity")
    soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0)
    temperature: Optional[float] = Field(None, ge=-20.0, le=60.0)
    recent_rainfall_mm: Optional[float] = Field(0.0, ge=0.0)
    forecast_rainfall_mm: Optional[float] = Field(0.0, ge=0.0)


class IrrigationRecommendationResponse(BaseModel):
    action: str  # IRRIGATE_IMMEDIATELY, IRRIGATE_LIGHT, MAINTAIN_MONITORING, DEFER_DUE_TO_RAIN
    recommended_water_mm: float
    urgency: str  # HIGH, MODERATE, LOW, NONE
    reason: str
    factors_evaluated: Dict[str, Any]
    recommendation_engine: str
    sensor_freshness: str
    limitations: str
