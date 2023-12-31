import os
import html
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from commands import Command

client_id = os.environ.get('FOURSQUARE_CLIENT_ID')
client_secret = os.environ.get('FOURSQUARE_CLIENT_SECRET')
base_url = os.environ.get('FOURSQSARE_API_URL')
foursquare_auth_key = os.environ.get('FOURSQUARE_API_KEY')

    
class Restauraunts(Command):
    def execute(self, update: Update, context: CallbackContext) -> None:
        city_name = self.get_city_name(context)
        restaurants = self.get_restauraunts(city_name)
        
        context.user_data['affordable_eats'] = restaurants
        update.message.reply_text(f"Here are some affordable places to eat in {city_name}, sorted by rating:", reply_markup=self.get_affordable_eats_keyboard(context))
        
        self.post_restauraunts(update, context, restaurants)
    
    def format_address_as_link(self, address: str):
        google_maps_link = f'https://www.google.com/maps/search/?api=1&query={html.escape(address)}'
        return f'<a href="{google_maps_link}">{html.escape(address)}</a>'
    
    def get_affordable_eats_keyboard(self, context: CallbackContext) -> InlineKeyboardMarkup:
        city_name = self.get_city_name(context)
        return ReplyKeyboardMarkup([[KeyboardButton("🔙 Back")], [KeyboardButton(f"🥗 Show me more restaurants in {city_name}!")]])
    
    def get_venue_photos(self, venue_id: str) -> str:
        url = f'https://api.foursquare.com/v3/places/{venue_id}/photos'
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
        }
        
        headers = {
            "accept": "application/json",
            "Authorization": foursquare_auth_key
        }

        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            photos = response.json()
            if photos:
                venue_photo_url = f"{photos[0].get('prefix')}300x300{photos[0].get('suffix')}"
                return venue_photo_url
        else:
            return []

    
    def get_restauraunts(self, city_name: str) -> list:
        # https://location.foursquare.com/developer/reference/response-fields
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'near': city_name,
            'query': 'restaurants',
            'limit': 10,
            'fields' :'name,location,fsq_id,distance,link',  
            'sort': 'rating'
        }

        headers = {
            "accept": "application/json",
            "Authorization": foursquare_auth_key
        }

        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            venues = data.get('results')
            for venue in venues:
                venue_id = venue.get('fsq_id')
                venue['photo'] = self.get_venue_photos(venue_id)
            return venues
        else:
            return []
    
    def get_city_name(self, context: CallbackContext) -> str:
        city_data = context.user_data.get('city_data')[0]
        address_components = city_data.get('address_components')[0]
        city_name = address_components.get('long_name')
        return city_name
    
    def post_restauraunts(self, update: Update, context: CallbackContext, restaurants: list) -> None:
        for restaurant in restaurants:
            restaurant_name = restaurant.get('name')
            restaurant_location = restaurant.get('location').get('formatted_address')
            restaurant_photo = restaurant.get('photo')
            
            if restaurant_photo:
                update.message.reply_photo(photo=restaurant_photo)
            
            restaurant_location_as_link = self.format_address_as_link(restaurant_location)
            message_text = f"{restaurant_name}\n{restaurant_location_as_link}"
            update.message.reply_text(message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)