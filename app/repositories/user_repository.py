from sqlalchemy.orm import Session
from app.models.user import User, UserRole


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        return self.db.query(User).count()

    def listar(self) -> list[User]:
        """Todos los usuarios, del más reciente al más antiguo."""
        return self.db.query(User).order_by(User.created_at.desc()).all()

    def contar_admins(self) -> int:
        """Cuántos administradores hay. Sirve para no quedarse sin ninguno."""
        return self.db.query(User).filter(User.role == UserRole.ADMIN.value).count()