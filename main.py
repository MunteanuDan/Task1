from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

API_KEY = '68d4825531ad4e45822132305242102'



class WeatherForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    max_temp = db.Column(db.Float, nullable=False)
    min_temp = db.Column(db.Float, nullable=False)
    total_precip = db.Column(db.Float, nullable=False)
    sunrise = db.Column(db.String(50), nullable=False)
    sunset = db.Column(db.String(50), nullable=False)

    __table_args__ = (db.UniqueConstraint('date', 'city', name='unique_date_city'),)



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form['city']
        response = fetch_weather_forecast(city)
        if response:
            save_forecast_to_db(response, city)
            forecasts = response['forecast']['forecastday']
        else:
            forecasts = []
        return render_template_string(TEMPLATE, forecasts=forecasts, city=city)
    return render_template_string(TEMPLATE)

def fetch_weather_forecast(city):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days=3"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def save_forecast_to_db(forecast, city):
    for day in forecast['forecast']['forecastday']:
        existing_forecast = WeatherForecast.query.filter_by(date=day['date'], city=city).first()
        if existing_forecast:
            db.session.delete(existing_forecast)
            db.session.commit()


        weather = WeatherForecast(
            date=day['date'],
            city=city,
            max_temp=day['day']['maxtemp_c'],
            min_temp=day['day']['mintemp_c'],
            total_precip=day['day']['totalprecip_mm'],
            sunrise=day['astro']['sunrise'],
            sunset=day['astro']['sunset'],
        )
        db.session.add(weather)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


TEMPLATE = '''
<!doctype html>
<html>
<head><title>Weather Forecast</title></head>
<body>
    <h2>Enter a city to get the weather forecast</h2>
    <form method="post">
        <input type="text" name="city" required>
        <button type="submit">Submit</button>
    </form>
    {% if forecasts %}
        <h3>Weather Forecast for {{ city }}</h3>
        <table border="1">
            <tr>
                <th>Date</th>
                <th>Max Temp (C)</th>
                <th>Min Temp (C)</th>
                <th>Total Precipitation (mm)</th>
                <th>Sunrise</th>
                <th>Sunset</th>
            </tr>
            {% for forecast in forecasts %}
                <tr>
                    <td>{{ forecast['date'] }}</td>
                    <td>{{ forecast['day']['maxtemp_c'] }}</td>
                    <td>{{ forecast['day']['mintemp_c'] }}</td>
                    <td>{{ forecast['day']['totalprecip_mm'] }}</td>
                    <td>{{ forecast['astro']['sunrise'] }}</td>
                    <td>{{ forecast['astro']['sunset'] }}</td>
                </tr>
            {% endfor %}
        </table>
    {% endif %}
</body>
</html>
'''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
