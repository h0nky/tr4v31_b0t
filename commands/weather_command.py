import os
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from commands import Command

weather_api_key = os.environ.get('OPEN_WEATHER_API_KEY')

class Weather(Command):
    def execute(self, update: Update, context: CallbackContext) -> None:
        city_coordinates = self.get_city_coordinates(context)
        weather_now = self.get_weather_forecast(city_coordinates)
        weather_desc = weather_now.get('daily')[0].get('summary')
        update.message.reply_text(f'Here is the weather forecast for your destination: {weather_desc}', reply_markup=self.get_weather_keyboard())
        pass

    def get_city_coordinates(self, context: CallbackContext) -> str:
        city_data = context.user_data.get('city_data')[0]
        lat = city_data.get('geometry').get('location').get('lat')
        lng = city_data.get('geometry').get('location').get('lng')
        return {'lat': lat, 'lng': lng}
    
    def get_weather_forecast(self, city_coordinates: dict) -> list:
        lat = city_coordinates.get("lat")
        lon = city_coordinates.get("lng")
        appid = '23f15497c341cb62b6878982f298236f'
        weather_url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={appid}'

        response = requests.get(weather_url)

        if response.status_code == 200:
            weather_data = response.json()
            return weather_data
        else:
            return []
    
    def get_weather_keyboard(self) -> InlineKeyboardMarkup:
        # Return the InlineKeyboardMarkup with the "Back to Lobby" button
        back_to_lobby_button = KeyboardButton("🔙 Back")
        more_landmarks_button = KeyboardButton("☀️ Tell me more about current weather!")
        keyboard = [[back_to_lobby_button], [more_landmarks_button]]
        return ReplyKeyboardMarkup(keyboard)