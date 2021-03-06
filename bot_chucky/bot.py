import requests as r

from .constants import API_URL
from .errors import BotChuckyInvalidToken, BotChuckyTokenError
from .helpers import (FacebookData, GmailData,
                      SoundCloudData, StackExchangeData,
                      TwitterData, WeatherData)


class BotChucky:
    def __init__(self, token, open_weather_token=None,
                 tw_consumer_key=None, tw_consumer_secret=None,
                 tw_access_token_key=None, tw_access_token_secret=None,
                 soundcloud_id=None):
        """
        :param token: Facebook Token, required
        :param open_weather_token: not required
        :param tw_consumer_key: Twitter Consumer Key, not required
        :param tw_consumer_secret: Twitter Consumer Secret, not required
        :param tw_access_token_key: Twitter Access Token Key, not required
        :param tw_access_token_secret: Twitter Access Token Secret,
        not required
        :param headers: Set default headers for the graph API, default
        :param fb: Instace of FacebookData class, default
        :param weather: Instace of WeatherData class, default
        :param twitter: Instance of TwitterData class, default
        :param soundcloud_id: SoundCloud Access Token, not required
        :param stack: Instance of StackExchange class, not required
        """
        self.token = token
        self.open_weather_token = open_weather_token
        self.params = {'access_token': self.token}
        self.headers = {'Content-Type': 'application/json'}
        self.fb = FacebookData(self.token)
        self.weather = WeatherData(open_weather_token)
        self.twitter_tokens = {
            'consumer_key': tw_consumer_key,
            'consumer_secret': tw_consumer_secret,
            'access_token_key': tw_access_token_key,
            'access_token_secret': tw_access_token_secret
        }
        self.twitter = TwitterData(self.twitter_tokens)
        self.soundcloud_id = soundcloud_id
        self.soundcloud = SoundCloudData(self.soundcloud_id)
        self.stack = StackExchangeData()
        self.gmail = GmailData()

    def send_message(self, id_: str, text):
        """
        :param  id_: User facebook id, type -> str
        :param text: some text, type -> str
        """
        data = {
            'recipient': {'id': id_},
            'message': {'text': text}
        }
        message = r.post(API_URL, params=self.params,
                         headers=self.headers, json=data)
        if message.status_code is not 200:
            return message.text

    def send_weather_message(self, id_: str, city_name: str):
        """
        :param id_: User facebook id, type -> str
        :param city_name: Find weather by city name
        :return send_message function, send message to a user,
        with current weather
        """
        if self.open_weather_token is None:
            raise BotChuckyTokenError('Open Weather')

        weather_info = self.weather.get_current_weather(city_name)
        if weather_info['cod'] == 401:
            error = weather_info['message']
            raise BotChuckyInvalidToken(error)

        if weather_info['cod'] == '404':
            msg = 'Sorry I cant find information ' \
                  'about weather in {0}, '.format(city_name)

            return self.send_message(id_, msg)

        description = weather_info['weather'][0]['description']
        msg = 'Current weather in {0} is: {1}'.format(city_name, description)
        return self.send_message(id_, msg)

    def send_tweet(self, status: str):
        """
        :param status: Tweet text, type -> str
        """
        if not all(self.twitter_tokens.values()):
            raise BotChuckyTokenError('Twitter')

        reply = self.twitter.send_tweet(status)

        if reply['success']:
            return f'I have placed your tweet with status \'{status}\'.'

        return f'Twitter Error: {reply["detail"]}.'

    def send_soundcloud_message(self, id_: str, artist: str):
        """
        :param id_: User facebook id, type -> str
        :param artist: artist to search for, type -> str
        :return send_message function
        """
        if not self.soundcloud_id:
            raise BotChuckyTokenError('SoundCloud')
        result = self.soundcloud.search(artist)

        if result['success']:
            tracks_from_artist = list(result['tracks'].title)
            msg = f'SoundCloud found {result["artists"]}, \n' \
                  f'Track Listing: {tracks_from_artist}'
            return self.send_message(id_, msg)

        msg = f'SoundCloud Error: {result["detail"]}'

        return self.send_message(id_, msg)

    def send_stack_questions(self, id_, **kwargs):
        """
        :param id_: a User id
        :param kwargs: find by title='Update Django'
                               tag='Django'
        :return: send_message function, send message to a user with questions
        """
        msg = 'I can\'t find questions for you;( try again'
        answers = self.stack.get_stack_answer_by(**kwargs)

        if answers:
            if len(answers) > 2:
                msg = f'I found questions for you, links below\n\n ' \
                      f'Question 1: {answers[0]}\n' \
                      f'Question 2: {answers[1]}'
                return self.send_message(id_, msg)

            if len(answers) == 1:
                msg = f'I found question for you, link below\n\n ' \
                      f'Question: {answers[0]}'
                return self.send_message(id_, msg)
        else:
            return self.send_message(id_, msg)

    def send_mail(self, to, subject, body):
        """
        :param to: Email address of the receiver
        :param subject: Subject of the email
        :param body: Body of the email
        """
        reply = self.gmail.send_mail(to, subject, body)

        if reply['success']:
            return f'Sent mail successfully to {to}'

        return f'Gmail Error: {reply["detail"]}'
