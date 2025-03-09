import datetime
import calendar
from sqlalchemy import select
from components.dbmodel import DutyCalendar, Duty
from components import session

year = 2025
month = 3
_, num_of_days = calendar.monthrange(year, month)
# 定义三个组的成员
A_group = ["陈雪莲", "邱凌", "卓燕斌", "万米",
           "包云飞", "沈毅", "蒋炯明", "王仲晖",
           "徐蒲金", "秦刚", "胡继云", "刘敏",
           "郭天赐", "孙俊敏", "陈栋"]
B_group = ["张南", "徐升", "余行方"]
C_group = ["祁玉权", "何超超"]

# 确定本次排班的天数，以便确定人员数量和顺序
start = datetime.date(year, month, 1)
end = datetime.date(year, month, num_of_days)
stmt = select(DutyCalendar).where(DutyCalendar.type == "inproduct"
                                  and
                                  DutyCalendar.date.between(start, end))
rows = session.execute(stmt).scalars().all()
inproduct_dates = [row.date for row in rows]
max_a_group = len(A_group) if len(A_group) <=len(inproduct_dates) else len(rows)
max_b_group = len(B_group) if len(B_group) <= len(inproduct_dates) else len(rows)

inproduct_a_group = list()
substitute_a_group = list()
for person in A_group:
    stmt = select(Duty).where(Duty.type == "inproduct" and Duty.employee == person).order_by(Duty.date.desc())
    rows = session.execute(stmt).scalars().all()
    if rows:
        substitute_a_group.append(rows[0])
    else:
        inproduct_a_group.append(person)
inproduct_a_group = sorted(inproduct_a_group, key=lambda duty: duty.date)
if len(inproduct_a_group) < max_a_group:
    inproduct_a_group += substitute_a_group[:max_a_group - len(inproduct_a_group)]

