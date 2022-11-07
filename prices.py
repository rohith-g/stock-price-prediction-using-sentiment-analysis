import os
import numpy
import pandas as pd

# Logging imports
import logging
from logging.handlers import RotatingFileHandler

# Constants
new_dir = './prices_sentiment/'
stocks = ['AMZN', 'APPL', 'FB', 'MSFT', 'TSLA']
fields = ['Date', 'Adj Close', 'Volume']


def setup_logging(screen_output=False):
    logger = logging.getLogger("prices")
    logger.setLevel(logging.DEBUG)

    if not os.path.exists("./logs"):
        os.makedirs("./logs")

    file_handler = RotatingFileHandler('./logs/prices.log', maxBytes=1000000, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                                                datefmt="%Y-%m-%d %H:%M:%S %Z"))
    logger.addHandler(file_handler)


def get_prices_dir(stock):
    return './prices_raw/%s/'%(stock)


def get_tweets_file(stock, file):
    return './tweets_analysed/%s/%s'%(stock, file)


def create_stock_dicts():
    df_dict = {}
    for stock in stocks:
        prices_dir = get_prices_dir(stock)
        files = os.listdir(prices_dir)
        dfs = [pd.read_csv(os.path.join(prices_dir, f), usecols=fields) for f in files]
        df = pd.concat(dfs, ignore_index=True)
        df_dict[stock] = df
    return df_dict


def get_sentiment_values(file_path):
    # If matching analysed tweets csv file found for that day
    sentiment_df = pd.read_csv(file_path, skipinitialspace=True, usecols=['score','sentiment'])

    # Tweet counts of each sentiment per day
    total_len = len(sentiment_df.index)
    pos_count = sentiment_df[sentiment_df['sentiment'] == 'pos']['sentiment'].count()
    neg_count = sentiment_df[sentiment_df['sentiment'] == 'neg']['sentiment'].count()
    neu_count = sentiment_df[sentiment_df['sentiment'] == 'neu']['sentiment'].count()

    # Percentage of each sentiment per day
    if (total_len > 0):
        pos_percent = round((pos_count / total_len), 3)
        neg_percent = round((neg_count / total_len), 3)
        neu_percent = round((neu_count / total_len), 3)
    else:
        pos_percent = 0
        neg_percent = 0
        neu_percent = 0

    return [total_len, pos_percent, neg_percent, neu_percent]


def create_csv(stock, prices_df, tweets_df):
    # Joining prices dataframe and sentiment dataframe in one
    df_concat = pd.concat([prices_df, tweets_df], axis=1)
    df_concat['price_diff'] = df_concat['Adj Close'].diff()
    df_concat['stock_trend'] = numpy.where(df_concat["price_diff"] > 0, 1, 0)
    
    # Remove rows without any sentiment analysis
    df_concat = df_concat[df_concat.twitter_volume.notnull()]
    
    # Creating final csv file per stock
    filename = stock + '.csv'
    new_file = os.path.join(new_dir, filename)
    df_concat.to_csv(new_file, index=False)


def main():
    setup_logging()
    logging.getLogger("prices").info("Starting")

    df_dict = create_stock_dicts()
    logging.getLogger("prices").info("Created dictionary of prices dataframes for all stocks")

    for stock, prices_df in df_dict.items():
        tweets_df = pd.DataFrame(columns=['twitter_volume', 'pos_percent', 'neg_percent', 'neu_percent'])
        logging.getLogger("prices").info(f"Created tweets_df for stock: '{stock}'")

        # Iterate through each day in prices dataframe
        for index, row in prices_df.iterrows():
            file = '%s.csv'%(row['Date'])
            file_path = get_tweets_file(stock, file)

            if os.path.exists(file_path):
                # If matching analysed tweets csv file for that day
                counts = get_sentiment_values(file_path)
                tweets_df.loc[len(tweets_df.index)] = counts
                logging.getLogger("prices").debug(f"Counts for file: '{file_path}' are '{counts}")
            else:
                # If no matching analysed tweets csv file for that day
                tweets_df.loc[len(tweets_df.index)] = [None, None, None, None]
                logging.getLogger("prices").debug(f"file: '{file_path}' does not exist, so adding none values")

        # Create final csv
        create_csv(stock, prices_df, tweets_df)
        logging.getLogger("prices").debug(f"Created final csv for stock: '{stock}'")


if __name__ == "__main__":
    main()