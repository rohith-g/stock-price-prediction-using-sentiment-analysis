import re
import os
import string
import emoji
import fnmatch

# Dataframe imports
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

# Logging imports
import logging
from logging.handlers import RotatingFileHandler

# Sentiment Analysis imports
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Constants
fields = ['date', 'time', 'tweet', 'language']
stocks = ['AMZN', 'APPL', 'FB', 'MSFT', 'TSLA']


def setup_logging(screen_output=False):
    logger = logging.getLogger("sentiment")
    logger.setLevel(logging.DEBUG)

    if not os.path.exists("./logs"):
        os.makedirs("./logs")

    file_handler = RotatingFileHandler('./logs/sentiment.log', maxBytes=1000000, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                                                datefmt="%Y-%m-%d %H:%M:%S %Z"))
    logger.addHandler(file_handler)


def raw_tweets_dir(stock):
    return './tweets_raw/%s/csv/'%(stock)


def calculated_sentiment_tweets_dir(stock):
    new_dir = './tweets_analysed/%s/'%(stock)
    os.makedirs(new_dir, exist_ok=True)    
    return new_dir


def drop_non_eng(df):
    eng_only_df = df.drop(df[df.language != 'en'].index)
    eng_only_df = eng_only_df.drop(columns=['language'])
    eng_only_df = eng_only_df.reset_index(drop=True)
    return eng_only_df


def remove_malformed_rows(file):
    # Get the start string
    f = open(file,"r")
    first_line = f.readline()
    second_line = f.readline()
    lines = f.readlines()
    f.close()
    
    # Remove the malformed rows
    f = open(file,"w")
    f.write(first_line)
    for line in lines:
        if line.startswith(second_line[0:2]):
            f.write(line)
    f.close()


def cleaning_stopwords(text):
    return " ".join([word for word in str(text).split() if word not in set(stopwords.words("english"))])


def cleaning_punctuations(text):
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)


def cleaning_repeating_char(text):
    return re.sub(r'(.)1+', r'1', text)


def cleaning_URLs(text):
    return re.sub('((www.[^s]+)|(https?://[^s]+))',' ',text)


def cleaning_numbers(text):
    return re.sub('[0-9]+', '', text)


def cleaning_emojis(text):
    return emoji.replace_emoji(text, replace='')


def clean_tweets(tweets):
    tweets['tweet_cleaned'] = tweets['tweet'].apply(lambda x: cleaning_stopwords(x))
    tweets['tweet_cleaned'] = tweets['tweet_cleaned'].apply(lambda x: cleaning_punctuations(x))
    tweets['tweet_cleaned'] = tweets['tweet_cleaned'].apply(lambda x: cleaning_repeating_char(x))
    tweets['tweet_cleaned'] = tweets['tweet_cleaned'].apply(lambda x: cleaning_URLs(x))
    tweets['tweet_cleaned'] = tweets['tweet_cleaned'].apply(lambda x: cleaning_numbers(x))
    tweets['tweet_cleaned'] = tweets['tweet_cleaned'].apply(lambda x: cleaning_emojis(x))
    return tweets


def calculate_sentiment(tweets):
    polarity = ['neg', 'neu', 'pos']
    tweets['score'] = tweets['tweet_cleaned'].apply(lambda x: SentimentIntensityAnalyzer().polarity_scores(x)["compound"])
    tweets['sentiment'] = np.select([tweets['score'] < 0, tweets['score'] == 0, tweets['score'] > 0], polarity)
    return tweets


def main(skip_exists=True):
    setup_logging()
    logging.getLogger("sentiment").info("Starting")

    for stock in stocks:
        raw_dir = raw_tweets_dir(stock)
        logging.getLogger("sentiment").info(f"Working on stock: '{stock}'")
        logging.getLogger("sentiment").info(f"Raw tweets directory: '{raw_dir}'")

        count = 0
        len_dir = len(fnmatch.filter(os.listdir(raw_dir), '*.csv'))

        for filename in os.listdir(raw_dir):
            count += 1
            logging.getLogger("sentiment").debug(f"File: {count}/{len_dir}")

            new_dir = calculated_sentiment_tweets_dir(stock)
            new_file = os.path.join(new_dir, filename)

            if (os.path.exists(new_file) & skip_exists):
                logging.getLogger("sentiment").debug(f"Skipping '{filename}' as '{new_file}' exists")
                continue

            file = os.path.join(raw_dir, filename)
            remove_malformed_rows(file)
            logging.getLogger("sentiment").debug(f"Removed malformed rows for '{filename}'")

            try:
                tweets_df = pd.read_csv(file, usecols=fields)
                tweets_df = drop_non_eng(tweets_df)
                tweets_df = clean_tweets(tweets_df)
                logging.getLogger("sentiment").debug(f"Finished cleaning dataset and tweets for '{filename}'")
            except Exception:
                logging.getLogger("sentiment").error(f"Error occucured when reading from csv '{filename}'")
                continue

            try:
                tweets_df = calculate_sentiment(tweets_df)
                logging.getLogger("sentiment").debug(f"Finished calculating sentiment for '{filename}'")
            except Exception:
                logging.getLogger("sentiment").error(f"Error occucured when calculating sentiment for '{filename}'")
                continue

            tweets_df.to_csv(new_file, index=False)
            logging.getLogger("sentiment").debug(f"Exporting csv to '{new_file}'")


if __name__ == "__main__":
    main()