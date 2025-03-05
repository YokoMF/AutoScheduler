from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine('sqlite:///db.sqlite')
session = Session(engine)
