"""Agricultural intelligence and explainable irrigation recommendation routers."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.recommendation import (
    CropModelMetricsResponse,
    CropRecommendationRequest,
    CropRecommendationResponse,
    IrrigationRecommendationRequest,
    IrrigationRecommendationResponse,
)
from app.services.irrigation_service import recommend_irrigation
from app.services.ml_crop_service import get_crop_recommender

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/crop", response_model=CropRecommendationResponse)
def recommend_crop_endpoint(payload: CropRecommendationRequest):
    recommender = get_crop_recommender()
    result = recommender.predict(
        N=payload.N,
        P=payload.P,
        K=payload.K,
        temperature=payload.temperature,
        humidity=payload.humidity,
        ph=payload.ph,
        rainfall=payload.rainfall,
        soil_moisture=payload.soil_moisture,
    )
    return result


@router.get("/crop/metrics", response_model=CropModelMetricsResponse)
def get_crop_metrics_endpoint():
    recommender = get_crop_recommender()
    return recommender.get_metrics()


@router.post("/irrigation", response_model=IrrigationRecommendationResponse)
def recommend_irrigation_endpoint(payload: IrrigationRecommendationRequest, db: Session = Depends(get_db)):
    result = recommend_irrigation(
        db=db,
        field_id=payload.field_id,
        crop_type=payload.crop_type,
        growth_stage=payload.growth_stage,
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
        recent_rainfall_mm=payload.recent_rainfall_mm,
        forecast_rainfall_mm=payload.forecast_rainfall_mm,
    )
    return result


@router.get("/irrigation/{field_id}", response_model=IrrigationRecommendationResponse)
def get_field_irrigation_recommendation(field_id: str, db: Session = Depends(get_db)):
    result = recommend_irrigation(db=db, field_id=field_id)
    return result
