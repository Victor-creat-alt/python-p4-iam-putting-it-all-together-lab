from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String)
    image_url = db.Column(db.String, default="")
    bio = db.Column(db.String, default="")

    # Recipes association (One-to-Many relationship)
    recipes = db.relationship('Recipe', back_populates='user', cascade="all, delete-orphan")

    serialize_rules = ('-recipes.user',)  # Prevent circular serialization

    # Setter for password (use this to securely set a password hash)
    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty.")
        self._password_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')

    # Validator for password
    def validate_password(self, password):
        if not self._password_hash:
            raise ValueError("Password hash has not been set.")
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    # Protect Password Hash Attribute
    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hash is protected.")

    # Validates username is not empty and unique
    @validates('username')
    def validate_username(self, key, value):
        if not value:
            raise ValueError("Username cannot be empty.")
        if User.query.filter(User.username == value).first():
            raise ValueError("Username must be unique.")
        return value

    # Add this initializer to handle passwords during object creation
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)  # Add this line
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False, default=0)

    # Validates the length of instructions
    @validates('instructions')
    def validate_instructions_length(self, key, value):
        if len(value) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return value

    # Validates title is not empty
    @validates('title')
    def validate_title(self, key, value):
        if not value:
            raise ValueError("Title cannot be empty.")
        return value

    # User Association
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='recipes')

    serialize_rules = ('-user.recipes',) # Prevent circular serialization

    # Validates user_id presence
    @validates('user_id')
    def validate_user_id(self, key, value):
        if not value:
            raise ValueError("Recipe must be associated with a user.")
        return value