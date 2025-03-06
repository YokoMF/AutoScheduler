from sqlalchemy import select, func
from components.dbmodel import HolidayCalendar
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


stmt = select(HolidayCalendar).where(HolidayCalendar.holiday != 0)
rows = session.execute(stmt).scalars().all()
for row in rows:
    print(row.date, row.holiday, row.comefrom)