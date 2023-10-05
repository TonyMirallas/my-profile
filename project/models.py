# models.py

from flask_login import UserMixin
import pandas as pd
from . import db
import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), unique=True)
    twitter_users = db.relationship('Twitter_User', secondary='user_twitter_user', backref='users')

class Twitter_User(db.Model):
    __tablename__ = 'twitter_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    image = db.Column(db.String(1000))
    date = db.Column(db.String(100))
    twitter_user_infos = db.relationship('Twitter_User_Info', backref='twitter_user')
    tweets = db.relationship('Tweet', backref='twitter_user')
    
    def __init__(self, name, image=''):
        self.name = name
        self.image = image
        date = datetime.datetime.now()

# many to many relationship between users and twitter_users
user_twitter_user = db.Table('user_twitter_user', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('twitter_user_id', db.Integer, db.ForeignKey('twitter_user.id')),
    db.Column('notifications', db.Boolean, default=False)    
)

class Twitter_User_Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)
    biography = db.Column(db.String(1000))
    location = db.Column(db.String(1000))
    date = db.Column(db.String(100))
    twitter_user_id = db.Column(db.Integer, db.ForeignKey('twitter_user.id'))

    def __init__(self, followers=0, following=0, biography='', location=''):
        self.followers = followers
        self.following = following
        self.biography = biography
        self.location = location
        date = datetime.datetime.now()

    @staticmethod
    def get_stats(twitter_user):

        stats = {}
        twitter_user_info = twitter_user.twitter_user_infos[0]
        followers = twitter_user_info.followers
        following = twitter_user_info.following

        followers_growth = 0
        following_growth = 0

        if len(twitter_user.twitter_user_infos) > 1:
            twitter_user_info = twitter_user.twitter_user_infos[1]
            followers_growth = followers - twitter_user_info.followers
            following_growth = following - twitter_user_info.following

        stats['followers'] = followers
        stats['following'] = following
        stats['followers_growth'] = followers_growth
        stats['following_growth'] = following_growth

        return stats

class Tweet(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    long_date = db.Column(db.String(100))
    _date = db.Column(db.String(100))
    _account = db.Column(db.String(100))
    text = db.Column(db.String(1000))
    _state = db.Column(db.String(100))
    reply = db.Column(db.Integer)
    retweet = db.Column(db.Integer)
    like = db.Column(db.Integer)
    twitter_user_id = db.Column(db.Integer, db.ForeignKey('twitter_user.id'))

    def __init__(self, long_date='', date=0, account = '', text='', state = 'none', reply = 0, retweet = 0, like = 0):
        self.long_date = long_date
        self._date = date
        self._account = account
        self.text = text
        self._state = state
        self.reply = reply
        self.retweet = retweet
        self.like = like

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, long_date):
        self._date = long_date
        if "T" in long_date:
            self._date = long_date.partition("T")[0]

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, account):
        self._account = '@' + account.split('@')[1].split('·')[0].strip()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        STATES = ['retwitteó', 'retweet', 'Tweet fijado']
        self._state = state
        if state in STATES[0]:
            self._state = STATES[1]
            
    def __str__(self) -> str:
        return f'date: {self.date}, long_date: {self.long_date}, account: {self.account}, text: {self.text}, state: {self.state}, reply: {self.reply}, retweet: {self.retweet}, like: {self.like}'

    def as_dict(self):
        return {'date': self.date, 'long_date': self.long_date, 'account': self.account, 'text': self.text, 'state': self.state, 'reply': self.reply, 'retweet': self.retweet, 'like': self.like}

    @staticmethod
    def delete_all():
        Tweet.query.delete()
        db.session.commit()

    @staticmethod
    def get_all(twitter_user=None):
        if twitter_user:
            return Tweet.query.filter_by(twitter_user_id=twitter_user.id).all()
        return Tweet.query.all()

    @staticmethod
    def get_stats(twitter_user=None, date=None):

        tweets = Tweet.get_all(twitter_user)

        if date:
            tweets = [tweet for tweet in tweets if datetime.datetime.strptime(tweet.date, '%Y-%m-%d').date() >= date]

        df = pd.DataFrame([tweet.as_dict() for tweet in tweets])                    

        # get stats
        test = len(df)
        stats = {}
        stats['tweets'] = len(df)
        stats['total_retweets'] = len(df[df['state'] == 'Retweet'])
        stats['total_tweets'] = df[df['state'].isin(['Retweet', 'Tweet fijado'])]
        stats['average_retweets'] = int(round(stats['total_tweets']['retweet'].mean(), 0))
        stats['average_retweets_std'] = round(stats['total_tweets']['retweet'].std(), 2)
        stats['average_likes'] = int(round(stats['total_tweets']['like'].mean(), 0))
        stats['average_likes_std'] = round(stats['total_tweets']['like'].std(), 2)
        stats['average_replies'] = int(round(stats['total_tweets']['reply'].mean(), 0))
        stats['average_replies_std'] = round(stats['total_tweets']['reply'].std(), 2)
        
        return stats