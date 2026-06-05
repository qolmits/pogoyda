from fastapi import APIRouter, HTTPException, status
from models import ConsensusWeatherResponse, WeatherProviderData, FavoriteCityRequest, FavoriteCityResponse, HourlyForecastItem, DailyForecastItem
import random
import json
import os
from datetime import datetime, timedelta

router = APIRouter()
DB_FILE = "favorites_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = [{"id": 1, "city_name": "Київ"}, {"id": 2, "city_name": "Черкаси"}]
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def clamp(n, minn, maxn):
    return max(min(n, maxn), minn)

def generate_hourly(base_temp, base_wind, base_hum, seed_val):
    random.seed(seed_val)
    hourly = []
    hours = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]
    for h in hours:
        time_factor = -3 if h in ["00:00", "04:00"] else (3 if h in ["12:00", "16:00"] else 0)
        hourly.append(HourlyForecastItem(
            time=h,
            temperature=round(base_temp + time_factor + random.uniform(-1, 1), 1),
            wind_speed=round(clamp(base_wind + random.uniform(-2, 2), 0, 30), 1),
            humidity=clamp(base_hum + random.randint(-10, 10), 0, 100)
        ))
    return hourly

def fetch_mock_weather(city: str):
    random.seed(city.lower())
    base_temp = random.uniform(5.0, 28.0)
    base_hum = random.randint(40, 85)
    base_wind = random.uniform(2.0, 12.0)
    base_press = random.randint(745, 765)

    conditions = ["Сонячно", "Мінлива хмарність", "Хмарно", "Дощ"]
    cond = random.choice(conditions)

    p1_temp, p2_temp, p3_temp = base_temp + random.uniform(-1, 1), base_temp + random.uniform(-2, 2), base_temp + random.uniform(-1.5, 1.5)
    p1_wind, p2_wind, p3_wind = base_wind + random.uniform(-1, 1), base_wind + random.uniform(-2, 2), base_wind + random.uniform(-1, 1)

    return [
        WeatherProviderData(
            provider_name="OpenWeather", temperature=round(p1_temp, 1), humidity=clamp(base_hum + random.randint(-5, 5), 0, 100),
            wind_speed=round(clamp(p1_wind, 0, 30), 1), pressure=base_press + random.randint(-2, 2), condition=cond,
            hourly=generate_hourly(p1_temp, p1_wind, base_hum, city.lower() + "op")
        ),
        WeatherProviderData(
            provider_name="WeatherBit", temperature=round(p2_temp, 1), humidity=clamp(base_hum + random.randint(-8, 8), 0, 100),
            wind_speed=round(clamp(p2_wind, 0, 30), 1), pressure=base_press + random.randint(-4, 4), condition=cond if random.random() > 0.3 else "Хмарно",
            hourly=generate_hourly(p2_temp, p2_wind, base_hum, city.lower() + "wb")
        ),
        WeatherProviderData(
            provider_name="AccuWeather", temperature=round(p3_temp, 1), humidity=clamp(base_hum + random.randint(-4, 4), 0, 100),
            wind_speed=round(clamp(p3_wind, 0, 30), 1), pressure=base_press + random.randint(-1, 1), condition=cond,
            hourly=generate_hourly(p3_temp, p3_wind, base_hum, city.lower() + "aw")
        )
    ]

@router.get("/api/weather", response_model=ConsensusWeatherResponse)
def get_consensus_weather(city: str):
    if not city.strip():
        raise HTTPException(status_code=400, detail="Назва міста не може бути порожньою")

    providers_data = fetch_mock_weather(city)

    random.seed(city.lower() + "geo")
    lat, lon = round(random.uniform(44.0, 52.0), 4), round(random.uniform(22.0, 40.0), 4)

    avg_temp = sum(p.temperature for p in providers_data) / len(providers_data)
    avg_hum = sum(p.humidity for p in providers_data) / len(providers_data)
    avg_wind = sum(p.wind_speed for p in providers_data) / len(providers_data)
    avg_press = sum(p.pressure for p in providers_data) / len(providers_data)

    # Генерація прогнозу на 5 днів (консенсусна логіка)
    daily_forecast = []
    current_date = datetime.now()
    conditions = ["Сонячно", "Мінлива хмарність", "Хмарно", "Дощ"]

    for i in range(1, 6):
        future_date = current_date + timedelta(days=i)
        random.seed(city.lower() + str(i))
        daily_forecast.append(DailyForecastItem(
            date=future_date.strftime("%d.%m"),
            temperature=round(avg_temp + random.uniform(-4, 4), 1),
            wind_speed=round(clamp(avg_wind + random.uniform(-3, 3), 0, 25), 1),
            condition=random.choice(conditions)
        ))

    return {
        "city": city.capitalize(), "lat": lat, "lon": lon, "providers": providers_data,
        "consensus_temperature": round(avg_temp, 1), "consensus_humidity": round(avg_hum, 1),
        "consensus_wind_speed": round(avg_wind, 1), "consensus_pressure": int(round(avg_press)),
        "daily_forecast": daily_forecast
    }

@router.get("/api/favorites", response_model=list[FavoriteCityResponse])
def get_favorites(): return load_db()

@router.post("/api/favorites", response_model=FavoriteCityResponse, status_code=status.HTTP_201_CREATED)
def add_favorite(payload: FavoriteCityRequest):
    if not payload.city_name.strip(): raise HTTPException(status_code=400, detail="Порожня назва")
    db = load_db()
    if any(c["city_name"].lower() == payload.city_name.strip().lower() for c in db):
        raise HTTPException(status_code=400, detail="Вже є в обраному")
    new_id = max([c["id"] for c in db], default=0) + 1
    new_favorite = {"id": new_id, "city_name": payload.city_name.capitalize()}
    db.append(new_favorite)
    save_db(db)
    return new_favorite

@router.delete("/api/favorites/{city_id}")
def delete_favorite(city_id: int):
    db = load_db()
    if not any(c["id"] == city_id for c in db): raise HTTPException(status_code=404, detail="Не знайдено")
    db = [c for c in db if c["id"] != city_id]
    save_db(db)
    return {"message": "Успішно видалено"}
