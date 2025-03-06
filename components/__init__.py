from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import logging.config
import yaml

engine = create_engine('sqlite:///db.sqlite')
session = Session(engine)

with open("conf/logging.yaml", 'r', encoding='utf-8') as file:
        log_config = yaml.safe_load(file)
        logging.config.dictConfig(log_config)