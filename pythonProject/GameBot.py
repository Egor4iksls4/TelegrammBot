import telebot
from telebot import types
from GameAPI import GameAPI


class GameBot:
    def __init__(self, token, api_key):
        self.bot = telebot.TeleBot(token)
        self.api = GameAPI(api_key)
        self.waiting_for_genre = False
        self.setup_handlers()

    def setup_handlers(self) -> None:
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message, custom_message="Привет! Выберите, что вы ищете.") -> None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ['Найти игру', 'Ожидаемые релизы', 'Help']
            markup.add(*buttons)
            self.bot.send_message(message.chat.id, custom_message, reply_markup=markup)

        @self.bot.message_handler(func=lambda message: message.text == 'Найти игру')
        def show_genre_buttons(message) -> None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ['Action', 'Indie', 'Shooter', 'Другое', 'Назад']
            markup.add(*buttons)
            self.bot.send_message(message.chat.id, "Выберите жанр игры:", reply_markup=markup)

        @self.bot.message_handler(func=lambda message: message.text == 'Назад')
        def go_back(message) -> None:
            send_welcome(message, "Вы вернулись назад.")

        @self.bot.message_handler(func=lambda message: message.text in ['Action', 'Indie', 'Shooter'])
        def handle_predefined_genres(message) -> None:
            genre = message.text.strip().lower()
            self.api.fetch_and_send_games(self.bot, message.chat.id, genre)

        @self.bot.message_handler(func=lambda message: message.text == 'Другое')
        def handle_other_genre(message) -> None:
            self.waiting_for_genre = True
            self.bot.send_message(message.chat.id, "Пожалуйста, введите ваш жанр:")

        @self.bot.message_handler(func=lambda message: self.waiting_for_genre)
        def get_custom_genre(message) -> None:
            genre = message.text.strip().lower()
            self.waiting_for_genre = False
            self.api.fetch_and_send_games(self.bot, message.chat.id, genre)

        @self.bot.message_handler(func=lambda message: message.text == 'Help')
        def send_help(message) -> None:
            genres = self.api.fetch_genres()
            if genres:
                response_message = ('Здесь можно найти не все жанры игр, но вот некоторые из них, которые вы можете '
                                    'найти: \n'
                                    + "\n".join(genres))
                self.bot.send_message(message.chat.id, response_message)
            else:
                self.bot.send_message(message.chat.id, "Ошибка при получении жанров.")

        @self.bot.message_handler(func=lambda message: message.text == 'Ожидаемые релизы')
        def ask_for_number_of_releases(message) -> None:
            self.bot.send_message(message.chat.id, "Сколько релизов вы хотите увидеть?")

        @self.bot.message_handler(func=lambda message: True)
        def send_releases(message):
            self.api.process_number_of_images(self.bot, message)

    def run(self) -> None:
        self.bot.infinity_polling()