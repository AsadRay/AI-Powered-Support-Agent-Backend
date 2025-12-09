from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('Secret_Key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('Database_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['GROQ_API_KEY'] = os.getenv('Groq_API_Key')
    app.config['JWT_SECRET'] = os.getenv('JWT_Secret')
    
    db.init_app(app)
    migrate.init_app(app, db)

    from app.models.chat import ChatMessage
    from app.routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')
    
    return app