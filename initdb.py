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

holidays = list()
workdays = list()
# 春节
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

workdays.append(datetime.date(2025, 1, 26))
workdays.append(datetime.date(2025, 2, 8))

# 元旦
holidays.append(datetime.date(2025, 1, 1))

# 清明
holidays.append(datetime.date(2025, 4, 4))
workdays.append(datetime.date(2025, 4, 27))

# 劳动节
labors = [datetime.date(2025, 5, 1),
          datetime.date(2025, 5, 2),
          datetime.date(2025, 5, 3),
          datetime.date(2025, 5, 4),
          datetime.date(2025, 5, 5),]
records = [HolidayCalendar(date=d, holiday=4, comefrom="系统") for d in labors]
for record in records:
    session.merge(record)
session.commit()

holidays.append(datetime.date(2025, 6, 2))
workdays.append(datetime.date(2025, 9, 28))

# 国庆节
national = [datetime.date(2025, 10, 1),
            datetime.date(2025, 10, 2),
            datetime.date(2025, 10, 3),
            datetime.date(2025, 10, 4),
            datetime.date(2025, 10, 5),
            datetime.date(2025, 10, 5),
            datetime.date(2025, 10, 6),
            datetime.date(2025, 10, 7),
            datetime.date(2025, 10, 8)]
records = [HolidayCalendar(date=d, holiday=3, comefrom="系统") for d in national]
for record in records:
    session.merge(record)
session.commit()

workdays.append(datetime.date(2025, 10, 11))

records = [HolidayCalendar(date=d, holiday=6, comefrom="系统") for d in holidays]
for record in records:
    session.merge(record)
session.commit()

records = [HolidayCalendar(date=d, holiday=0, comefrom="系统") for d in workdays]
for record in records:
    session.merge(record)
session.commit()
