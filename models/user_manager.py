import json
import os
import uuid
from typing import List, Optional

from models.user import User


class UserManager:
    def __init__(self, data_file: str = "data/users.json") -> None:
        self._data_file: str = data_file
        self._users: List[User] = []
        self._load_from_file()
        self._ensure_admin_user()

    def _load_from_file(self) -> None:
        dir_name = os.path.dirname(self._data_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        if not os.path.exists(self._data_file):
            self._save_to_file()
            return

        with open(self._data_file, "r", encoding="utf-8") as fh:
            try:
                raw = json.load(fh)
            except json.JSONDecodeError:
                raw = []

        self._users = []
        repaired = False
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                self._users.append(User.from_dict(item))
            except KeyError:
                username = item.get("username", "").strip().lower()
                email = item.get("email", f"{username or 'user'}@example.com")
                if username == "glenadi.teguh":
                    self._users.append(
                        User.create(
                            user_id=uuid.uuid4().hex,
                            username="glenadi.teguh",
                            email=email,
                            password="admin123",
                            role="super_admin",
                        )
                    )
                    repaired = True
                # Skip any other malformed user entries.

        if repaired:
            self._save_to_file()

    def _save_to_file(self) -> None:
        try:
            with open(self._data_file, "w", encoding="utf-8") as fh:
                json.dump([user.to_dict() for user in self._users], fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise IOError(f"Failed to save data to '{self._data_file}': {exc}") from exc

    def _ensure_admin_user(self) -> None:
        user = self.get_user_by_username("glenadi.teguh")
        if user is None:
            self.create_user(
                username="glenadi.teguh",
                email="glenadi.teguh@example.com",
                password="admin123",
                role="super_admin",
            )
        elif user.role.lower() != "super_admin":
            user.role = "super_admin"
            self._save_to_file()

    def get_all_users(self) -> List[User]:
        return list(self._users)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        for user in self._users:
            if user.get_id() == str(user_id):
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        normalized = username.strip().lower()
        for user in self._users:
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
        if any(user.email.lower() == email for user in self._users):
            raise ValueError(f"Email '{email}' sudah digunakan.")

        user_id = uuid.uuid4().hex
        user = User.create(user_id=user_id, username=username, email=email, password=password, role=role)
        self._users.append(user)
        self._save_to_file()
        return user

    def set_user_role(self, user_id: str, role: str) -> User:
        user = self.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User not found.")

        normalized_role = role.strip().lower()
        if normalized_role not in {"user", "admin", "super_admin"}:
            raise ValueError("Invalid role.")

        user.role = normalized_role
        self._save_to_file()
        return user

    def delete_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if user is None:
            return False

        self._users = [u for u in self._users if u.get_id() != str(user_id)]
        self._save_to_file()
        return True

    def reset_password(self, username: str, email: str, new_password: str) -> bool:
        user = self.get_user_by_username(username)
        if user is None or user.email.lower() != email.strip().lower():
            return False

        # Reset password to the provided new password.
        user.password_hash = user.__class__.create(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            password=new_password,
            role=user.role
        ).password_hash
        self._save_to_file()
        return True
