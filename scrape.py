import os
import twint
import logging
from logging.handlers import RotatingFileHandler
from datetime import date, timedelta


search_strings = {
    "AMZN": "$AMZN OR #AMZN",
    "APPL": "$APPL OR #APPL",
    "FB": "$FB OR #FB",
    "MSFT": "$MSFT OR #MSFT",
    "TSLA": "$TSLA OR #TSLA"
}


def setup_logging(screen_output=False):
    logger = logging.getLogger("scrape")
    logger.setLevel(logging.DEBUG)

    if not os.path.exists("./logs"):
        os.makedirs("./logs")

    file_handler = RotatingFileHandler('./logs/scrape.log', maxBytes=1000000, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                                                datefmt="%Y-%m-%d %H:%M:%S %Z"))
    logger.addHandler(file_handler)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def main(start_date, end_date, skip_exists=True):
    setup_logging()
    logging.getLogger("scrape").info("Starting")
    logging.getLogger("scrape").info(f"Scraping tweets between '{str(start_date)}' and '{str(end_date)}'")

    for single_date in daterange(start_date, end_date):
        for stock, terms in search_strings.items():
            output_file = "./tweets_raw/" + stock + "/csv/" + str(single_date.strftime("%Y-%m-%d")) + ".csv"

            # Check if file exists
            if (os.path.exists(output_file) & skip_exists):
                logging.getLogger("scrape").debug(f"Stock: '{stock}' Date: '{str(single_date)}' [EXISTS]")
            else:
                try:
                    c = twint.Config()
                    c.Search = terms
                    c.Lang = "en"
                    c.Since = str(single_date.strftime("%Y-%m-%d")) + ' 00:00:00'
                    c.Until = str(single_date.strftime("%Y-%m-%d")) + ' 23:59:59'
                    c.Output = output_file
                    c.Hide_output = True
                    c.Store_csv = True
                    twint.run.Search(c)
                    logging.getLogger("scrape").debug(f"Stock: '{stock}' Date: '{str(single_date)}' [DONE]")
                except Exception:
                    logging.getLogger("scrape").error(f"Stock: '{stock}' Date: '{str(single_date)}' [FAILED]")
                    pass


if __name__ == "__main__":
    # Configuration
    skip = True
    start_date = date(2020, 8, 1)
    end_date = date(2021, 6, 1)

    main(start_date, end_date, skip)