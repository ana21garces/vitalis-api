from sqlalchemy.orm import Session
from app.models.survey import SurveyResponse


class SurveyRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, response: SurveyResponse) -> SurveyResponse:
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def get_by_user_id(self, user_id) -> SurveyResponse | None:
        return self.db.query(SurveyResponse).filter(
            SurveyResponse.user_id == user_id
        ).first()

    def has_completed(self, user_id) -> bool:
        return self.get_by_user_id(user_id) is not None