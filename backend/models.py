from pydantic import BaseModel
from typing import List

class HourlyForecastItem(BaseModel):
    time: str
    temperature: float
    wind_speed: float
    humidity: int

class DailyForecastItem(BaseModel):
    date: str
    temperature: float
    wind_speed: float
    condition: str

class WeatherProviderData(BaseModel):
    provider_name: str
    temperature: float
    humidity: int
    wind_speed: float
    pressure: int
    condition: str
    hourly: List[HourlyForecastItem]

class ConsensusWeatherResponse(BaseModel):
    city: str
    lat: float
    lon: float
    providers: List[WeatherProviderData]
    consensus_temperature: float
    consensus_humidity: float
    consensus_wind_speed: float
    consensus_pressure: int
    daily_forecast: List[DailyForecastItem]

class FavoriteCityRequest(BaseModel):
    city_name: str

class FavoriteCityResponse(BaseModel):
    id: int
    city_name: str
