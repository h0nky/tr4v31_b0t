import os
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from messages import WELCOME_MESSAGE_LONG, WELCOME_MESSAGE_CONCISE
from command import TouristAttractionsCommand, WeatherForecastCommand, AffordableEatsCommand, LocalPhrasesCommand, TravelTipsCommand, FiveFactsCommand, HelpCommand, BackCommand

telegram_bot_token = os.environ.get('TELEGRAM_TOKEN')
bot_username = os.environ.get('BOT_USERNAME')
google_map_api_key = os.environ.get('GOOGLE_MAP_API_KEY')
geocoding_api_url = os.environ.get('GEOCODING_API_URL')

TOURIST_ATTRACTIONS = '🗽 Sites'
WEATHER_FORECAST = '☀️ Weather'
AFFORDABLE_EATS = '🥗 Eats'
LOCAL_PHRASES = '🗣 Phrases'
TRAVEL_TIPS = '🎯 Tips'
FIVE_FACTS = '🎲 Facts'
HELP = '❓ Help'
BACK = '🔙 Back'

# Define states for the conversation
DESTINATION, LOBBY = range(2)


user_choice_to_command = {
    TOURIST_ATTRACTIONS: TouristAttractionsCommand(),
    WEATHER_FORECAST: WeatherForecastCommand(),
    AFFORDABLE_EATS: AffordableEatsCommand(),
    LOCAL_PHRASES: LocalPhrasesCommand(),
    TRAVEL_TIPS: TravelTipsCommand(),
    FIVE_FACTS: FiveFactsCommand(),
    HELP: HelpCommand(),
    BACK: BackCommand()
}


def fetch_city_data(city_name: str, google_api_key: str, geocoding_api_url: str, context: CallbackContext):
    req_params = {
        "address": city_name,
        "key": google_api_key
    }

    response = requests.get(geocoding_api_url, params=req_params)

    try:
        data = response.json()
    except ValueError as e:
        return f"Error parsing JSON: {e}"

    if data.get('status') == 'OK':
        context.user_data['city_data'] = data['results']
        return data['results']
    else:
        return f"No city was found! Status: {data.get('status')}"


# Function to handle the user's destination input
def handle_user_input(update: Update, context: CallbackContext):
    user_name = update.message.chat.first_name
    user_input = update.message.text

    city_data = fetch_city_data(user_input, google_map_api_key, geocoding_api_url, context)

    if city_data == 'No city was found! Status: ZERO_RESULTS':
        update.message.reply_text("🤷‍♂️ Excusez-moi but no city was found... Try again!")
    else:
        update.message.reply_text(
            f"🔥 Awesome, {user_name}! You're traveling to {user_input}!",
            reply_markup=get_lobby_keyboard()
        )

        return LOBBY


def handle_message(update: Update, context: CallbackContext):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User({update.message.chat.id}) in {message_type} : "{text}"')
    
    # This block is to handle cases when you want to mention [travel_bot] directly in group chat.
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
    print('Bot:', response)
    update.message.reply_text(response)


# Function to create the bot lobby keyboard
def get_lobby_keyboard():
    # Define the options in the lobby
    options = [
        [TOURIST_ATTRACTIONS, WEATHER_FORECAST, AFFORDABLE_EATS],
        [LOCAL_PHRASES, TRAVEL_TIPS, FIVE_FACTS],
        [HELP, BACK]
    ]
    # Create a list of KeyboardButton objects for each row of options
    keyboard = [[KeyboardButton(option) for option in row] for row in options]
    # Return the ReplyKeyboardMarkup with the lobby keyboard
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


# Function to handle user's choice in the lobby
def handle_lobby_choice(update: Update, context: CallbackContext):
    user_choice = update.message.text
    command = user_choice_to_command.get(user_choice)

    if user_choice == BACK:
        update.message.reply_text("What else can I help you with? 👀", reply_markup=get_lobby_keyboard())
        return LOBBY

    if command:
        command.execute(update, context)
    else:
        update.message.reply_text("Invalid choice. Please choose a valid option.")


def start(update: Update, context: CallbackContext):
    user_name = update.message.chat.first_name
    welcome_message = WELCOME_MESSAGE_CONCISE.format(user_name)
    update.message.reply_text(welcome_message)

    return DESTINATION


def cancel(update: Update, context: CallbackContext):
    user_name = update.message.chat.first_name
    update.message.reply_text(f"👋 Have a nice trip, {user_name}! Feel free to reach out again anytime!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


# Log errors
def error(update: Update, context: CallbackContext):
    print(f'Update {update} caused error {context.error}')


# Main function
def main() -> None:
    print('Starting bot...')

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Create the ConversationHandler to handle the onboarding process and lobby choices
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DESTINATION: [MessageHandler(Filters.text & ~Filters.command, handle_user_input)],
            LOBBY: [MessageHandler(Filters.text & ~Filters.command, handle_lobby_choice)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add the ConversationHandler to the dispatcher
    dispatcher.add_handler(conv_handler)

    # Errors
    dispatcher.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()