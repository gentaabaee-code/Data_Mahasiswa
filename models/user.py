from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin):
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        role: str = "user",
    ) -> None:
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def get_id(self) -> str:
        return str(self.user_id)

    @property
    def is_admin(self) -> bool:
        return self.role.lower() in {"admin", "super_admin"}

    @property
    def is_super_admin(self) -> bool:
        return self.role.lower() == "super_admin"

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            password_hash=data["password_hash"],
            role=data.get("role", "user"),
        )

    @classmethod
    def create(cls, user_id: str, username: str, email: str, password: str, role: str = "user") -> "User":
        return cls(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
        )
