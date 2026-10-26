from app import app
from db import initialise_database

if __name__ == "__main__":
    with app.app_context():
        initialise_database(force=True)
        print("Base de dados recriada com dados de demonstração.")
        print("Credenciais: consulte o README.md")
