from flask import Flask, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from config import Config
from extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    from models import User, Group, GroupMember, Message

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return {
            "message": "WhatsApp MVP Backend is running!"
        }

    # -----------------------------------
    # USER REGISTRATION
    # -----------------------------------
    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return {
                "error": "Name, email and password are required"
            }, 400

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return {
                "error": "User with this email already exists"
            }, 409

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return {
            "message": "User registered successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }, 201

    # -----------------------------------
    # USER LOGIN
    # -----------------------------------
    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {
                "error": "Email and password are required"
            }, 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return {
                "error": "Invalid email or password"
            }, 401

        if not check_password_hash(user.password, password):
            return {
                "error": "Invalid email or password"
            }, 401

        access_token = create_access_token(
            identity=str(user.id)
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }, 200

    # -----------------------------------
    # GET GROUP DETAILS
    # -----------------------------------
    @app.route("/api/groups/<int:group_id>", methods=["GET"])
    @jwt_required()
    def get_group(group_id):

        current_user_id = int(get_jwt_identity())

        group = Group.query.get(group_id)

        if not group:
            return {
                "error": "Group not found"
            }, 404

        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user_id
        ).first()

        if not membership:
            return {
                "error": "You are not a member of this group"
            }, 403

        members = []

        for member in group.memberships:
            members.append({
                "id": member.user.id,
                "name": member.user.name,
                "email": member.user.email,
                "role": member.role
            })

        return {
            "group": {
                "id": group.id,
                "name": group.name,
                "created_by": group.created_by,
                "members": members
            }
        }, 200

    # -----------------------------------
    # ADD MEMBER TO GROUP
    # -----------------------------------
    @app.route("/api/groups/<int:group_id>/members", methods=["POST"])
    @jwt_required()
    def add_member(group_id):

        # Get logged-in user from JWT
        current_user_id = int(get_jwt_identity())

        # Check whether group exists
        group = Group.query.get(group_id)

        if not group:
            return {
                "error": "Group not found"
            }, 404

        # Check whether logged-in user is a member
        admin = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user_id
        ).first()

        if not admin:
            return {
                "error": "You are not a member of this group"
            }, 403

        # Check whether logged-in user is admin
        if admin.role != "admin":
            return {
                "error": "Only group admin can add members"
            }, 403

        # Get user ID from request
        data = request.get_json()

        user_id = data.get("user_id")

        if not user_id:
            return {
                "error": "user_id is required"
            }, 400

        # Check whether user exists
        user = User.query.get(user_id)

        if not user:
            return {
                "error": "User not found"
            }, 404

        # Check whether user is already a member
        existing_member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id
        ).first()

        if existing_member:
            return {
                "error": "User is already a member of this group"
            }, 409

        # Add user to group
        new_member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role="user"
        )

        db.session.add(new_member)
        db.session.commit()

        return {
            "message": "User added to group successfully",
            "member": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": new_member.role,
                "group_id": group_id
            }
        }, 201
        # -----------------------------------
    # SEND MESSAGE
    # -----------------------------------
    @app.route("/api/groups/<int:group_id>/messages", methods=["POST"])
    @jwt_required()
    def send_message(group_id):

    # Get logged-in user
        current_user_id = int(get_jwt_identity())

        # Check whether group exists
        group = Group.query.get(group_id)

        if not group:
            return {
                "error": "Group not found"
            }, 404

        # Check whether user is a member
        member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user_id
        ).first()

        if not member:
            return {
                "error": "You are not a member of this group"
            }, 403

        # Get message from request
        data = request.get_json()

        message_text = data.get("message")

        if not message_text:
            return {
                "error": "Message is required"
            }, 400

        # Create message
        new_message = Message(
            group_id=group_id,
            user_id=current_user_id,
            message=message_text
        )

        db.session.add(new_message)
        db.session.commit()

        return {
            "message": "Message sent successfully",
            "data": {
                "id": new_message.id,
                "group_id": new_message.group_id,
                "user_id": new_message.user_id,
                "message": new_message.message,
                "created_at": new_message.created_at.isoformat()
            }
        }, 201


    # -----------------------------------
    # READ MESSAGES
    # -----------------------------------
    @app.route("/api/groups/<int:group_id>/messages", methods=["GET"])
    @jwt_required()
    def get_messages(group_id):

        # Get logged-in user
        current_user_id = int(get_jwt_identity())

        # Check whether group exists
        group = Group.query.get(group_id)

        if not group:
            return {
                "error": "Group not found"
            }, 404

        # Check whether user is a member
        member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user_id
        ).first()

        if not member:
            return {
                "error": "You are not a member of this group"
            }, 403

        # Get all messages
        messages = Message.query.filter_by(
            group_id=group_id
        ).order_by(
            Message.created_at.asc()
        ).all()

        result = []

        for msg in messages:
            result.append({
                "id": msg.id,
                "user_id": msg.user_id,
                "user_name": msg.user.name,
                "message": msg.message,
                "created_at": msg.created_at.isoformat()
            })

        return {
            "group_id": group_id,
            "messages": result
        }, 200
        # -----------------------------------
    # DELETE MESSAGE - ADMIN ONLY
    # -----------------------------------
    @app.route("/api/groups/<int:group_id>/messages/<int:message_id>", methods=["DELETE"])
    @jwt_required()
    def delete_message(group_id, message_id):

        # Get logged-in user
        current_user_id = int(get_jwt_identity())

        # Check whether group exists
        group = Group.query.get(group_id)

        if not group:
            return {
                "error": "Group not found"
            }, 404

        # Check whether logged-in user is a member
        member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user_id
        ).first()

        if not member:
            return {
                "error": "You are not a member of this group"
            }, 403

        # Only admin can delete messages
        if member.role != "admin":
            return {
                "error": "Only group admin can delete messages"
            }, 403

        # Find the message
        message = Message.query.filter_by(
            id=message_id,
            group_id=group_id
        ).first()

        if not message:
            return {
                "error": "Message not found"
            }, 404

        # Delete message
        db.session.delete(message)
        db.session.commit()

        return {
            "message": "Message deleted successfully",
            "message_id": message_id
        }, 200
        # Remove Member - Admin Only
    @app.route("/api/groups/<int:group_id>/members/<int:user_id>", methods=["DELETE"])
    @jwt_required()
    def remove_member(group_id, user_id):

        current_user_id = int(get_jwt_identity())

        # Check if current user is an admin of this group
        admin_membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user_id
        ).first()

        if not admin_membership:
            return {
                "error": "You are not a member of this group"
            }, 403

        if admin_membership.role != "admin":
            return {
                "error": "Only group admin can remove members"
            }, 403

        # Find the member to remove
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id
        ).first()

        if not membership:
            return {
                "error": "User is not a member of this group"
            }, 404

        # Prevent admin from removing themselves
        if user_id == current_user_id:
            return {
                "error": "Admin cannot remove themselves from the group"
            }, 400

        db.session.delete(membership)
        db.session.commit()

        return {
            "message": "Member removed successfully"
        }, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)