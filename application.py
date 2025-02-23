import os
import traceback

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
import psycopg2

# DB configuration
RDS_HOSTNAME = os.environ["host_server"]
RDS_PORT = os.getenv("db_server_port", 5432)  # Default PostgreSQL port
RDS_DB_NAME = os.environ["database_name"]
RDS_USERNAME = os.environ["db_username"]
RDS_PASSWORD = os.environ["db_password"]

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY"
# Updated DB URI for PostgreSQL using psycopg2 driver
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://{RDS_USERNAME}:{RDS_PASSWORD}@{RDS_HOSTNAME}:{RDS_PORT}/{RDS_DB_NAME}"

# Register the database instance to the app
db = SQLAlchemy(app)
migrate = Migrate(app, db)

try:
    print("Applying migrations")
    with app.app_context():
        upgrade()
    print("Migrations applied")
except Exception as e:
    print("Failed to apply migrations:", e)

# Add the Country model
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capital = db.Column(db.String(100))
    population = db.Column(db.Integer)
    is_landlocked = db.Column(db.Boolean, default=False)


@app.route("/countries", methods=["GET"])
def get_countries():
    countries = Country.query.all()
    result = [{
        "id": country.id,
        "name": country.name,
        "capital": country.capital,
        "population": country.population,
        "is_landlocked": country.is_landlocked,
    } for country in countries]
    return jsonify(result)

@app.route("/countries/<int:id>", methods=["GET"])
def get_country(id):
    country = Country.query.get_or_404(id)
    return jsonify({
        "id": country.id,
        "name": country.name,
        "capital": country.capital,
        "population": country.population,
        "is_landlocked": country.is_landlocked,
    })

@app.route("/countries", methods=["POST"])
def create_country():
    data = request.get_json() or {}
    new_country = Country(
        name=data.get("name"),
        capital=data.get("capital"),
        population=data.get("population"),
        is_landlocked=data.get("is_landlocked", False)
    )
    db.session.add(new_country)
    db.session.commit()
    return jsonify({"message": "Country created", "id": new_country.id}), 201

@app.route("/countries/<int:id>", methods=["PUT"])
def update_country(id):
    country = Country.query.get_or_404(id)
    data = request.get_json() or {}
    country.name = data.get("name", country.name)
    country.capital = data.get("capital", country.capital)
    country.population = data.get("population", country.population)
    country.is_landlocked = data.get("is_landlocked", country.is_landlocked)
    db.session.commit()
    return jsonify({"message": "Country updated"})

@app.route("/countries/<int:id>", methods=["DELETE"])
def delete_country(id):
    country = Country.query.get_or_404(id)
    db.session.delete(country)
    db.session.commit()
    return jsonify({"message": "Country deleted"})


# Return tracebacks for debugging purposes
@app.errorhandler(Exception)
def handle_exception(e):
    return traceback.format_exc(), 500


# Run the app (this is not used by Elastic Beanstalk)
if __name__ == "__main__":
    # Auto apply migrations before starting the app
    app.run()
