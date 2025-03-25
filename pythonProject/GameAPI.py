from typing import Union
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