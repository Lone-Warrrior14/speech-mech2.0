import logging

logging.basicConfig(filename='downloader.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    logging.info(message)

def log_error(message):
    logging.error(message)