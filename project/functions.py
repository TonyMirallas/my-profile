# main.py
from . import create_app
import os
from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager # Code 2
import pickle # serialize cookies and save on pkl file. Load cookies after that
import time
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
# import numpy as np
from . import db
from .models import Tweet, Twitter_User, Twitter_User_Info, User

def get_root_path(folder = None, file = None, extension = None):

    if file and extension:
        file = file + extension

    if folder and file:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), folder, file)

    else:
        return os.path.dirname(os.path.abspath(__file__))

# get filename path from twitter url
def get_filename_path(twitter_url, extension = None):
    if extension:
        filename = twitter_url.split("https://twitter.com/", 1)[1] + extension
    else:
        filename = twitter_url.split("https://twitter.com/", 1)[1]

    return filename

# SCRAPING FUNCTIONS
# ------------------

def format_number(n):

    if n == '':
        return 0

    texts = {
        'mil': 1000,
        'M': 1000000
    }
    eliminate = [' ', '.', 'Seguidores', 'Siguiendo']
    multiply = 1
    new_format = ','

    for key, value in texts.items():        
        if key in n:
            multiply *= value
            n = n.replace(key, '')
            break

    for word in eliminate:
        n = n.replace(word, '')

    if new_format in n:
        n_list = n.split(new_format)
        multiply /= 10**(len(n_list[1])) # Ex: 14,43 -> multipy = multiply / (10** len('43'))
        n = n.replace(new_format, '')
            
    n = int(n) * multiply
    
    return int(n)


def twitter_scraping(until_date, links):

    # If headless mode is on, then twitter opens on white mode, which changes css classes. Thats why headless is off

    options = Options()
    # options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options, executable_path=GeckoDriverManager().install()) # Code 3

    for link in links:

        driver.get(link)
        cookies = pickle.load(open(get_root_path('cookies', 'cookies', '.pkl'), "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

        driver.refresh()
        time.sleep(3)
        # driver.get_screenshot_as_file("screenshot.png")

        tweets = []
        exit = False
        STATES = ['retwitteó', 'Tweet fijado']
        STATES_OUTPUT = ['Retweet', 'Tweet Fijado']
        trends_comparator = []
        height = 400
        HEIGHT = 400
        TIME = 4

        # $x("//a[contains(@href, '/Zequiodzilla/following')]")

        name = get_filename_path(link)
        image = driver.find_element(By.XPATH, "//img[@alt='Abre foto de perfil']").get_attribute("src")
        twitter_user = Twitter_User(name, image)

        # Check if twitter_user is already in database
        if Twitter_User.query.filter_by(name=name).first():
            twitter_user = Twitter_User.query.filter_by(name=name).first()
            twitter_user.image = image
            db.session.commit()
        else:
            db.session.add(twitter_user)
            db.session.commit()

        print(twitter_user.id)

        profile_followers = '/' + name + '/followers'
        profile_following = '/' + name + '/following'

        biography = driver.find_element(By.XPATH, "//div[@data-testid='UserDescription']").text
        # location = driver.find_element(By.XPATH, "//div[@data-testid='UserProfileHeader_Items']/div[2]/div[2]/div[2]").text
        followers = format_number(driver.find_element(By.XPATH, f"//a[@href='{profile_followers}']").text)
        following = format_number(driver.find_element(By.XPATH, f"//a[@href='{profile_following}']").text)

        print(f'Biography: {biography}, Followers: {followers}, Following: {following}' )

        twitter_user_info = Twitter_User_Info(followers, following, biography)
        twitter_user.twitter_user_infos.append(twitter_user_info)
        db.session.add(twitter_user_info)

        while not exit:

            trends = driver.find_elements(By.XPATH, "//article[@role='article']")

            previous_height = driver.execute_script("return document.documentElement.scrollHeight") # document.body.scrollHeight bugged

            for trend in trends:

                tweet = Tweet()

                try: # tweet date
                    tweet.long_date = trend.find_element(By.XPATH, ".//time").get_attribute("datetime")
                    
                except NoSuchElementException:
                    tweet.long_date = "0001-01-01"

                try: # tweet text
                    tweet.text = trend.find_element(By.XPATH, ".//div[@class='css-901oao r-18jsvk2 r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0']").text
                    
                except NoSuchElementException:
                    tweet.text = ''

                try: # tweet state
                    tweet.state = trend.find_element(By.XPATH, ".//*[@data-testid='socialContext']").text.strip()
                except NoSuchElementException:
                    tweet.state = 'Tweet'

                try: # tweet iteractions
                    # iteractions = trend.find_element(By.XPATH, ".//div[@role='group']").text.splitlines()
                    tweet.reply = trend.find_element(By.XPATH, ".//div[@data-testid='reply']").text
                    tweet.retweet = trend.find_element(By.XPATH, ".//div[@data-testid='retweet']").text
                    tweet.like = trend.find_element(By.XPATH, ".//div[@data-testid='like']").text

                except NoSuchElementException:
                    tweet.reply, tweet.retweet, tweet.like = '', '', ''


                try: # tweet account
                    tweet.account = trend.find_element(By.XPATH, ".//div[@data-testid='User-Names']").text

                except NoSuchElementException:
                    tweet.account = '@error.error'

                tweet.date = tweet.long_date

                if not any(x.long_date == tweet.long_date for x in tweets) and tweet.date != "0001-01-01":

                    tweet.reply = format_number(tweet.reply)
                    tweet.retweet = format_number(tweet.retweet)
                    tweet.like = format_number(tweet.like)
                    state = tweet.state

                    # compare if state is in STATES strings
                    for i in range(len(STATES)):
                        if STATES[i] in state:
                            tweet.state = STATES_OUTPUT[i]
                            break

                    if tweet.state != STATES_OUTPUT[1] and Tweet.query.filter_by(long_date=tweet.long_date, text=tweet.text, _account=tweet.account, twitter_user_id=twitter_user.id).first():
                        print(f'tweet {tweet} already in database')
                        exit = True
                        break

                    db.session.add(tweet)
                    twitter_user.tweets.append(tweet)
                    tweets.append(tweet)

                    print(tweet)

                    if datetime.datetime.strptime(tweet.date, "%Y-%m-%d") > until_date and trends[len(trends) - 1] == trend:
                        driver.execute_script(f"window.scrollTo(0, {str(height)})")
                        time.sleep(TIME)
                        actual_height = driver.execute_script("return document.documentElement.scrollHeight")
                        print('not yet')

                        if actual_height == previous_height:
                            print("not new height --- end scrapping")
                            exit = True
                            break

                    elif datetime.datetime.strptime(tweet.date, "%Y-%m-%d") <= until_date and state not in STATES:
                        exit = True
                        print(f"End scraping with {tweet.long_date}")
                        break

                    elif trends[len(trends) - 1] == trend: # main tweet after date
                        driver.execute_script(f"window.scrollTo(0, {str(height)})")
                        time.sleep(TIME)
                        actual_height = driver.execute_script("return document.documentElement.scrollHeight")
                        print('not yet 2')

                        if actual_height == previous_height:
                            print("not new height --- end scrapping")
                            exit = True
                            break

                elif trends[len(trends) - 1] == trend:
                    driver.execute_script(f"window.scrollTo(0, {str(height)})")
                    time.sleep(TIME)
                    actual_height = driver.execute_script("return document.documentElement.scrollHeight")
                    print(f"Actual height {actual_height}")
                    print('not yet')

                    if actual_height == previous_height:
                        print("not new height --- end scrapping")
                        exit = True
                        break

                height+=HEIGHT

        db.session.commit()
        # df = pd.DataFrame([x.as_dict() for x in tweets])
        # df.to_csv(get_root_path('csv', get_filename_path(link), '.csv'))

    driver.close()
    print("----- Scraping finalized -----")

        # save cookies on cookies.pkl file
        # pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))


def notificate_user():

    app = create_app()

    with app.app_context():
        users = User.query.all()

        for user in users:
            if user.twitter_users:
                for twitter_user in user.twitter_users:
                    stats_tweets, stats_twitter_user_info = get_weekly_summary(twitter_user)
                    print(f"User {user} with twitter user {twitter_user} has {stats_tweets} tweets and {stats_twitter_user_info} twitter user info \n \n")

    
def get_weekly_summary(twitter_user):

    # get last 7 days
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)

    stats_tweets = Tweet.get_stats(twitter_user, last_week)
    stats_twitter_user_info = Twitter_User_Info.get_stats(twitter_user)

    return stats_tweets, stats_twitter_user_info

# GRAPHS FUNCTIONS
# ----------------
def pie_graph(tweets, filename):

    df = pd.DataFrame([x.as_dict() for x in tweets])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    """
    PIE GRAPH ABOUT PERCENTAGES 
    """
    state = pd.Series(df['state'])
    state_count = state.value_counts()
    state_count.plot(kind='pie', autopct='%1.0f%%')

    filename = filename + '_pie'
    filename = get_root_path('static', filename, '.png')

    # get filename from /static
    filename_image = filename.split('project')[1]

    # save graph as png
    plt.savefig(filename, transparent=True, bbox_inches='tight', pad_inches=0)

    return filename_image

def tweet_frequency_graph(tweets, filename):

    df = pd.DataFrame([x.as_dict() for x in tweets])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    """
    BAR GRAPH ABOUT TWEETING FREQUENCY
    """
    df_hist = pd.DataFrame()
    df_hist['date'] = df['date']
    df_hist['year'] = df_hist['date'].dt.year
    df_hist['month'] = df_hist['date'].dt.month
    df_hist['week'] = df_hist['date'].dt.isocalendar().week

    def my_func(row, type):
        if row['state'] == type:
            val = True
        else:
            val = False
        return val

    STATE = [ 'Tweet Fijado', 'Tweet', 'Retweet']

    df_hist[STATE[0]] = df.apply(my_func, type = STATE[0], axis=1) #axis 1 -> appy function to all rows (0 for columns)
    df_hist[STATE[1]] = df.apply(my_func, type = STATE[1], axis=1) #axis 1 -> appy function to all rows (0 for columns)
    df_hist[STATE[2]] = df.apply(my_func, type = STATE[2], axis=1) #axis 1 -> appy function to all rows (0 for columns)
    df_hist.groupby(by=['week', 'month', 'year']).sum().plot(kind="bar") # sum is for sum rows values and count for count rows

    filename = filename + '_hist'
    filename = get_root_path('static', filename, '.png')

    # get filename from /static
    filename_image = filename.split('project')[1]

    plt.savefig(filename, transparent=True, bbox_inches='tight', pad_inches=0)

    return filename_image

def line_graph(tweets, filename):

    df = pd.DataFrame([x.as_dict() for x in tweets])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    """
    LINE GRAPH ABOUT TWEETS PER DAY
    """
    df_line = pd.DataFrame()
    df_line['date'] = df['date']
    # df_line['year'] = df_line['date'].dt.year
    # df_line['month'] = df_line['date'].dt.month
    # df_line['week'] = df_line['date'].dt.isocalendar().week
    # df_line['day'] = df_line['date'].dt.day

    def my_func(row, type):
        if row['state'] == type:
            val = True
        else:
            val = False
        return val

    STATE = [ 'Tweet Fijado', 'Tweet', 'Retweet']

    df_line[STATE[0]] = df.apply(my_func, type = STATE[0], axis=1) #axis 1 -> appy function to all rows (0 for columns)
    df_line[STATE[1]] = df.apply(my_func, type = STATE[1], axis=1) #axis 1 -> appy function to all rows (0 for columns)
    df_line[STATE[2]] = df.apply(my_func, type = STATE[2], axis=1) #axis 1 -> appy function to all rows (0 for columns)
    # df_line.groupby(by=['day', 'month', 'year']).sum().plot(kind="line") # sum is for sum rows values and count for count rows
    df_test = df_line.groupby(by=['date'], as_index=False).sum() # sum is for sum rows values and count for count rows
    df_test2 = df_test[['Tweet', 'Retweet', 'date']]
    print(f"df_line: {df_test2}")
    df_test2['date'] = df_test2['date'].astype(str)
    df_test2.plot(kind="line", x='date', y=['Tweet', 'Retweet'])

    filename = filename + '_line'
    filename = get_root_path('static', filename, '.png')

    # get filename from /static
    filename_image = filename.split('project')[1]

    plt.savefig(filename, transparent=True, bbox_inches='tight', pad_inches=0)

    return filename_image

def popular_tweet(tweets):
    """
    TWEET WITH MORE LIKES, RETWEETS AND REPLIES
    """

    df = pd.DataFrame([x.as_dict() for x in tweets])
    # df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # get rows from df with column 'state' == 'Tweet' or 'Tweet Fijado'
    df2 = df.loc[(df['state'] == 'Tweet') | (df['state'] == 'Tweet Fijado')]
    return df2.loc[df2['retweet'].idxmax()]

    # get row from df with biggest sum of retweets, likes and replies and state == 'Tweet' or 'Tweet Fijado'
    # df3 = df2.loc[(df2['retweet'] + df2['like'] + df2['reply']).idxmax()]
    # print(df3)

def test_print():
    print("test print")