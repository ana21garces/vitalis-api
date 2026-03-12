from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.survey import SurveyResponse as SurveyModel
from app.schemas.survey import SurveySubmit, SurveyResponse
from app.repositories.survey_repository import SurveyRepository
from app.repositories.user_repository import UserRepository
from app.core.dependencies import get_current_user  # ajusta según tu proyecto

router = APIRouter(prefix="/survey", tags=["survey"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/submit", response_model=SurveyResponse)
def submit_survey(
    payload: SurveySubmit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    survey_repo = SurveyRepository(db)

    if survey_repo.has_completed(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya completó la encuesta"
        )

    response = SurveyModel(
        user_id=current_user.id,
        sexo=payload.sexo,
        ano_cursado=payload.ano_cursado,
        answers=payload.answers,
        score_nutricion=payload.score_nutricion,
        score_ejercicio=payload.score_ejercicio,
        score_responsabilidad_salud=payload.score_responsabilidad_salud,
        score_manejo_estres=payload.score_manejo_estres,
        score_soporte_interpersonal=payload.score_soporte_interpersonal,
        score_autoactualizacion=payload.score_autoactualizacion,
        score_total=payload.score_total,
    )
    return survey_repo.create(response)


@router.get("/status")
def survey_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    survey_repo = SurveyRepository(db)
    return {"completed": survey_repo.has_completed(current_user.id)}