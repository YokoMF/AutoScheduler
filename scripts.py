from sqlalchemy import select, func
from components.dbmodel import HolidayCalendar, DutyCalendar
from components import session
from datetime import date

springs = [date(2025, 1, 28),
           date(2025, 1, 29),
           date(2025, 1, 30),
           date(2025, 1, 31),
           date(2025, 2, 1),
           date(2025, 2, 2),
           date(2025, 2, 3),
           date(2025, 2, 4),]

records = [HolidayCalendar(date=d, holiday=2, comefrom="系统") for d in springs]
for record in records:
    session.merge(record)
session.commit()

others = [date(2025, 4, 4),
          date(2025, 4, 5),
          date(2025, 4, 6)]
records = [HolidayCalendar(date=d, holiday=5, comefrom="系统") for d in others]
for record in records:
    session.merge(record)
session.commit()

record = HolidayCalendar(date=date(2025, 4, 7), holiday=0, comefrom="系统")
session.merge(record)
session.commit()

stmt = select(HolidayCalendar).where(HolidayCalendar.holiday != 0)
rows = session.execute(stmt).scalars().all()
for row in rows:
    print(row.date, row.holiday, row.comefrom)

dutys = [DutyCalendar(date=date(2025, 3, 8), type="in_product", maintainer="system"),
         DutyCalendar(date=date(2025, 3, 9), type="in_product", maintainer="system")]
for duty in dutys:
    session.merge(duty)
    session.commit()

