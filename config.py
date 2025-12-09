import os

class Config:
    SECRET_KEY = os.getenv('Secret_Key')
    SQLALCHEMY_DATABASE_URI = os.getenv('Database_URL')
    GROQ_API_KEY = os.getenv('Groq_API_Key')
    JWT_SECRET = os.getenv('JWT_Secret')
    SQLALCHEMY_TRACK_MODIFICATIONS = False