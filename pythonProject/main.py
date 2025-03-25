from GameBot import GameBot

if __name__ == "__main__":
    RAWG_API_KEY = '089d92314af646edabf6d61f0c754cc3'
    TELEGRAM_TOKEN = '6505009797:AAHAA1KZtmiL42M_-tFoEKJRHCM-R7CIPB8'
    game_bot = GameBot(TELEGRAM_TOKEN, RAWG_API_KEY)
    game_bot.run()
