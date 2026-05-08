import os
import uuid
from typing import List, Optional

from firebase_config import db
from models.user import User

_COLLECTION = "users"
_DEFAULT_ADMIN_USERNAME = "glenadi.teguh"
_DEFAULT_ADMIN_EMAIL = "glenadi.teguh@example.com"
_DEFAULT_ADMIN_PASSWORD = "admin123"


class FirestoreUserManager:
    def __init__(self, seed_file: Optional[str] = None, collection: str = _COLLECTION) -> None:
        self._seed_file = seed_file
        self._collection = db.collection(collection)
        self._bootstrap_from_file()
        self._ensure_admin_user()

    def _bootstrap_from_file(self) -> None:
        if not self._seed_file or not os.path.exists(self._seed_file):
            return

        if next(self._collection.limit(1).stream(), None) is not None:
            return

        from models.user_manager import UserManager

        legacy_manager = UserManager(data_file=self._seed_file)
        for user in legacy_manager.get_all_users():
            self._collection.document(user.get_id()).set(user.to_dict())

    def _save_user(self, user: User) -> None:
        self._collection.document(user.get_id()).set(user.to_dict())

    def _ensure_admin_user(self) -> None:
        user = self.get_user_by_username(_DEFAULT_ADMIN_USERNAME)
        if user is None:
            self.create_user(
                username=_DEFAULT_ADMIN_USERNAME,
                email=_DEFAULT_ADMIN_EMAIL,
                password=_DEFAULT_ADMIN_PASSWORD,
                role="super_admin",
            )
            return

        if user.role.lower() != "super_admin":
            user.role = "super_admin"
            self._save_user(user)

    def get_all_users(self) -> List[User]:
        users = [User.from_dict(doc.to_dict()) for doc in self._collection.stream()]
        return sorted(users, key=lambda user: user.username.lower())

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        doc = self._collection.document(str(user_id)).get()
        if not doc.exists:
            return None
        return User.from_dict(doc.to_dict())

    def get_user_by_username(self, username: str) -> Optional[User]:
        normalized = username.strip().lower()
        for user in self.get_all_users():
            if user.username.lower() == normalized:
                return user
        return None

    def verify_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if user is None:
            return None
        return user if user.check_password(password) else None

    def create_user(self, username: str, email: str, password: str, role: str = "user") -> User:
        username = username.strip()
        email = email.strip().lower()
        role = role.strip().lower() or "user"

        if not username:
            raise ValueError("Username is required.")
        if not email:
            raise ValueError("Email is required.")
        if not password:
            raise ValueError("Password is required.")
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' sudah digunakan.")
        if any(user.email.lower() == email for user in self.get_all_users()):
            raise ValueError(f"Email '{email}' sudah digunakan.")

        user = User.create(
            user_id=uuid.uuid4().hex,
            username=username,
            email=email,
            password=password,
            role=role,
        )
        self._save_user(user)
        return user

    def set_user_role(self, user_id: str, role: str) -> User:
        user = self.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User not found.")

        normalized_role = role.strip().lower()
        if normalized_role not in {"user", "admin", "super_admin"}:
            raise ValueError("Invalid role.")

        user.role = normalized_role
        self._save_user(user)
        return user

    def delete_user(self, user_id: str) -> bool:
        ref = self._collection.document(str(user_id))
        if not ref.get().exists:
            return False

        ref.delete()
        return True

    def reset_password(self, username: str, email: str, new_password: str) -> bool:
        user = self.get_user_by_username(username)
        if user is None or user.email.lower() != email.strip().lower():
            return False

        user.password_hash = User.create(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            password=new_password,
            role=user.role,
        ).password_hash
        self._save_user(user)
        return True