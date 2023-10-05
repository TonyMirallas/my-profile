# main.py
import os
from . import functions
from . import db
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask import request

from .models import Tweet, Twitter_User, Twitter_User_Info, user_twitter_user
main = Blueprint('main', __name__)

# shed = BackgroundScheduler(daemon=True)
# shed.add_job(functions.notificate_user, 'interval', minutes=1)
# shed.start()

@main.route('/test')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


# allow post requests
@main.route('/', methods=['GET', 'POST'])
@login_required
# scrapping get request

def scrapping():

    link = "https://twitter.com/Zequiodzilla"
    tweets = None
    graphs = []
    following = []
    twitter_user = None
    twitter_user_info = None
    stats = None

    if request.method == 'POST':
        days = int(request.form.get('days'))
        link = request.form.get('link')

        today = datetime.datetime.today()
        today = today + datetime.timedelta(days=-days)

        name = functions.get_filename_path(link)

        functions.twitter_scraping(today, links=[link])
        twitter_user = Twitter_User.query.filter_by(name=name).first()
        twitter_user_info = twitter_user.twitter_user_infos[0]
        tweets =  Tweet.query.filter_by(twitter_user_id=twitter_user.id).all()
        stats = Tweet.get_stats(twitter_user)

        graphs.append(functions.pie_graph(tweets, name))
        graphs.append(functions.tweet_frequency_graph(tweets, name))
        graphs.append(functions.popular_tweet(tweets))
        graphs.append(functions.line_graph(tweets, name))

        if twitter_user in current_user.twitter_users:
            following.append("unfollow")
            following.append("Unfollow")
        else:
            following.append("follow")
            following.append("Follow")

    return render_template('index.html', twitter_user=twitter_user, following=following, twitter_user_info=twitter_user_info, stats=stats, graphs=graphs, name=current_user.name)

@main.route('/following', methods=['GET', 'POST'])
@login_required
def following():

    if request.method == 'POST' and request.form.get('follow'):

        twitter_user_id = request.form.get('follow')
        twitter_user = Twitter_User.query.filter_by(id=twitter_user_id).first()
        current_user.twitter_users.append(twitter_user)
        db.session.commit()

    elif request.method == 'POST' and request.form.get('unfollow'):

        twitter_user_id = request.form.get('unfollow')
        twitter_user = Twitter_User.query.filter_by(id=twitter_user_id).first()
        current_user.twitter_users.remove(twitter_user)
        db.session.commit()

    twitter_users = current_user.twitter_users
    
    return render_template('following.html', twitter_users=twitter_users, name=current_user.name)

@main.route('/delete_tweets', methods=['GET', 'POST'])
@login_required
def delete_tweets():
    Tweet.delete_all()
    return "All tweets deleted"

@main.route('/delete_tweets_id', methods=['GET', 'POST'])
@login_required
def delete_tweets_id():
    # delete tweet with id bigger than 24
    Tweet.query.filter(Tweet.id>=1).delete() 
    db.session.commit()

    # Tweet.query.filter_by(id 24).delete()
    return "All tweets deleted"

@main.route('/user_twitter_user', methods=['GET', 'POST'])
@login_required
def user_twtiter_user():
    functions.notificate_user()
    return "nice"