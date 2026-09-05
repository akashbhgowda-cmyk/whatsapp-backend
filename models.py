from datetime import datetime

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship(
        "GroupMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    messages = db.relationship(
        "Message",
        back_populates="user"
    )


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship(
        "GroupMember",
        back_populates="group",
        cascade="all, delete-orphan"
    )

    messages = db.relationship(
        "Message",
        back_populates="group",
        cascade="all, delete-orphan"
    )


class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("groups.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="user"
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    group = db.relationship(
        "Group",
        back_populates="memberships"
    )

    user = db.relationship(
        "User",
        back_populates="memberships"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "group_id",
            "user_id",
            name="unique_group_user"
        ),
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("groups.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    group = db.relationship(
        "Group",
        back_populates="messages"
    )

    user = db.relationship(
        "User",
        back_populates="messages"
    )