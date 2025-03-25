from typing import Union
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup as bs


class GameAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.number_of_images = 0

    @staticmethod
    def fetch_genres() -> Union[list[str], None]:
        url = 'https://rawg.io/genres'
        response = requests.get(url)

        if response.status_code == 200:
            soup = bs(response.content, 'html.parser')
            genre_elements = soup.find_all('div', class_='heading')
            genres = [element.get_text(strip=True) for element in genre_elements]
            return genres
        return None

    @staticmethod
    def fetch_latest_releases():
        url = 'https://rawg.io/video-game-releases'
        response = requests.get(url)

        if response.status_code == 200:
            soup = bs(response.content, 'html.parser')
            release_elements = soup.find_all('div', class_='game-card-medium')
            print(release_elements[0])

            if release_elements:
                latest_release = release_elements[1]
                title = latest_release.find('div', class_='heading').get_text(strip=True)
                release_date = latest_release.find('div', class_='game-card-about__desription').get_text(strip=True)
                return f"{title} - {release_date}"

            return "Не удалось получить информацию о новом релизе."

    def fetch_and_send_games(self, bot, chat_id, genre) -> None:
        genre_mapping = {
            'action': 'action',
            'indie': 'indie',
            'shooter': 'shooter',
            'другое': 'other'
        }

        genre_api = genre_mapping.get(genre, genre)
        url = f'https://api.rawg.io/api/games?genres={genre_api}&key={self.api_key}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            games = data.get('results', [])

            if not games:
                bot.send_message(chat_id, f"Игры в жанре '{genre}' не найдены. Попробуйте другой жанр.")
                return

            game_list = [game['name'] for game in games[:5]]
            response_message = f"Вот 5 примеров игр в жанре '{genre}':\n\n" + "\n".join(game_list)
        else:
            response_message = "Произошла ошибка с API, попробуйте позже."

        bot.send_message(chat_id, response_message)

    def process_number_of_images(self, bot, message) -> None:
        try:
            self.number_of_images = int(message.text)
            if self.number_of_images <= 0:
                raise ValueError("Количество фотографий должно быть больше 0.")
            self.send_images_waiting(bot, message)
        except ValueError:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.")
            bot.register_next_step_handler(message, lambda msg: self.process_number_of_images(bot, msg))

    def send_images_waiting(self, bot, message) -> None:
        response = requests.get("https://stopgame.ru/games")

        if response.status_code == 200:
            soup = bs(response.content, 'html.parser')
            img_tags = soup.find_all('img', class_='_image_1u499_16')[0:4]
            dates = soup.find_all('span', class_="_release-date_1u499_387")[0:4]

            count = min(self.number_of_images, len(img_tags))
            for i in range(count):
                img = img_tags[i]
                src = img.get('src')
                if src:
                    try:
                        bot.send_photo(message.chat.id, src, caption='Дата релиза - ' + dates[i].text)
                    except Exception as e:
                        print(f"Не удалось отправить изображение: {e}")

            if self.number_of_images > len(img_tags):
                bot.send_message(message.chat.id, "К сожалению, мы имеем информацию о датах выхода всего 4-х игр.")


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


if __name__ == "__main__":
    RAWG_API_KEY = '089d92314af646edabf6d61f0c754cc3'
    TELEGRAM_TOKEN = '6505009797:AAHAA1KZtmiL42M_-tFoEKJRHCM-R7CIPB8'
    game_bot = GameBot(TELEGRAM_TOKEN, RAWG_API_KEY)
    game_bot.run()
