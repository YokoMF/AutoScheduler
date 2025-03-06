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
    session.merge(day)
    current += datetime.timedelta(days=1)
    session.commit()

springs = [datetime.date(2025, 1, 28),
           datetime.date(2025, 1, 29),
           datetime.date(2025, 1, 30),
           datetime.date(2025, 1, 31),
           datetime.date(2025, 2, 1),
           datetime.date(2025, 2, 2),
           datetime.date(2025, 2, 3),
           datetime.date(2025, 2, 4),]

records = [HolidayCalendar(date=d, holiday=2, comefrom="系统") for d in springs]
for record in records:
    session.merge(record)
session.commit()
