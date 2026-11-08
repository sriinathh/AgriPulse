from enum import Enum
from pydantic import BaseModel, Field, field_validator
from math import isfinite
from typing import Dict, Any

from app.services.model_manager import ModelManager, ModelNotFoundError
from app.errors import AppError

from fastapi import APIRouter, Depends
router = APIRouter()



class PredictionRequest(BaseModel):
    # Numeric features with built‑in constraints for expected ranges
    days_after_sowing: int = Field(..., description="Number of days after sowing")
    soil_moisture_0600: float = Field(..., description="Soil moisture at 06:00 (mm)")
    soil_moisture_change_24h: float = Field(..., description="Change in soil moisture over previous 24h (mm)")
    temperature_0600: float = Field(..., description="Temperature at 06:00 (°C)")
    humidity_0600: float = Field(..., description="Relative humidity at 06:00 (%)")
    rain_prev24h_mm: float = Field(..., ge=0, description="Rainfall in previous 24h (mm)")
    rain_forecast_next24h_mm: float = Field(..., ge=0, description="Forecasted rain in next 24h (mm)")
    irrigation_prev7d_mm: float = Field(..., ge=0, description="Total irrigation in previous 7 days (mm)")
    days_since_irrigation: int = Field(..., ge=0, description="Days since last irrigation event")
    # Categorical features – use Enum for validation so unknown values produce a standard "unexpected value" message
    

    class CropType(str, Enum):
        wheat = "wheat"
        corn = "corn"
        soybean = "soybean"
        rice = "rice"
        barley = "barley"

    class SoilType(str, Enum):
        loam = "loam"
        clay = "clay"
        sandy = "sandy"
        silt = "silt"
        peat = "peat"

    class IrrigationType(str, Enum):
        drip = "drip"
        sprinkler = "sprinkler"
        flood = "flood"
        pivot = "pivot"

    class GrowthStage(str, Enum):
        germination = "germination"
        vegetative = "vegetative"
        flowering = "flowering"
        maturation = "maturation"
        harvest = "harvest"

    crop_type: str = Field(..., description="Crop type identifier")
    soil_type: str = Field(..., description="Soil type identifier")
    irrigation_type: IrrigationType = Field(..., description="Irrigation system type")
    growth_stage: GrowthStage = Field(..., description="Growth stage identifier")

    @field_validator('crop_type', mode='before')
    def validate_crop_type(cls, v):
        if v not in cls.CropType.__members__:
            raise ValueError(f"unexpected value; permitted: {', '.join(cls.CropType.__members__.keys())}")
        return v

    @field_validator('soil_type', mode='before')
    def validate_soil_type(cls, v):
        if v not in cls.SoilType.__members__:
            raise ValueError(f"unexpected value; permitted: {', '.join(cls.SoilType.__members__.keys())}")
        return v

    @field_validator('irrigation_type')
    def validate_irrigation_type(cls, v):
        if v not in cls.IrrigationType.__members__:
            raise ValueError(f"unexpected value; permitted: {', '.join(cls.IrrigationType.__members__.keys())}")
        return v

    
    
    @field_validator('days_after_sowing')
    def validate_days_after_sowing(cls, v):
        if v < 0:
            raise ValueError("ensure this value is greater than or equal to 0")
        return v
    @field_validator('growth_stage', mode='before')
    def validate_growth_stage(cls, v):
        if v not in cls.GrowthStage.__members__:
            raise ValueError(
                f"unexpected value; permitted: {', '.join(cls.GrowthStage.__members__.keys())}"
            )
        return v
    @field_validator('humidity_0600', mode='before')
    def validate_humidity(cls, v):
        if v < 0:
            raise ValueError("ensure this value is greater than or equal to 0")
        if v > 100:
            raise ValueError("ensure this value is less than or equal to 100")
        return v

    @field_validator('*', mode='before')
    def check_finite(cls, v, info):        # Ensure numeric values are finite and reject NaN strings explicitly
        if isinstance(v, (int, float)):
            if not isfinite(v):
                raise ValueError("value is not a valid float")
        elif isinstance(v, str) and v.lower() == "nan":
            raise ValueError("value is not a valid float")
        return v
class PredictionResponse(BaseModel):
    irrigation_mm: float = Field(..., description="Predicted irrigation amount in millimeters")
    model_name: str = Field(..., description="Name of the model used for prediction")
    details: Dict[str, Any] | None = Field(None, description="Optional diagnostic information")


def get_model_manager() -> ModelManager:
    from app.services.model_manager import manager
    return manager


@router.post("/irrigation/predict", response_model=PredictionResponse)
async def predict_irrigation(request: PredictionRequest, manager: ModelManager = Depends(get_model_manager)):
    try:
        raw_features = request.model_dump()
        prediction = manager.predict(raw_features)
        return PredictionResponse(
            irrigation_mm=prediction,
            model_name="irrigation_model",
            details={"features_used": list(raw_features.keys())},
        )
    except ModelNotFoundError as e:
        raise AppError(status_code=500, code="model_not_found", message=str(e))
    except Exception as e:
        raise AppError(status_code=500, code="prediction_error", message="Unexpected error during prediction", details=str(e))
