from sqlalchemy.orm import Session
import datetime
from components import engine
from components.dbmodel import Base, HolidayCalendar

Base.metadata.create_all(engine)

start = datetime.date(2025, 1, 1)
end = datetime.date(2025, 12, 31)
current = start

session = Session(engine)
while current <= end:
    day = HolidayCalendar(date=current, holiday=1 if current.weekday() in [5, 6] else 0, comefrom="系统")
    session.add(day)
    current += datetime.timedelta(days=1)
    session.commit()
