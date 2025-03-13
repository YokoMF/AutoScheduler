from datetime import date
from sqlalchemy import select, func
from components.dbmodel import Duty, DutyCalendar
from components import session

daily = [
    Duty(date=date(2025,3,31), employee="包云飞", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 28), employee="王仲晖", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 27), employee="胡继云", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 26), employee="蒋炯明", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 25), employee="孙俊敏", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 24), employee="邱凌", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 21), employee="沈毅", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 20), employee="郭天赐", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 19), employee="陈栋", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 18), employee="万米", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 12), employee="刘敏", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 4), employee="卓燕斌", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 10), employee="徐蒲金", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 7), employee="陈雪莲", type="uat-night", taskid="default"),
    Duty(date=date(2025, 3, 3), employee="秦刚", type="uat-night", taskid="default"),
]

weekend = [
    Duty(date=date(2025, 3, 29), employee="刘敏", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 30), employee="郭天赐", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 16), employee="卓燕斌", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 15), employee="陈雪莲", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 9), employee="邱凌", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 8), employee="沈毅", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 1), employee="万米", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 2), employee="胡继云", type="uat-weekend", taskid="default"),
    Duty(date=date(2025,2,22), employee="包云飞", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 30), employee="何超超", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 29), employee="徐升", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 22), employee="张南", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 23), employee="祁玉权", type="uat-weekend", taskid="default"),
    Duty(date=date(2025, 3, 15), employee="余行方", type="uat-weekend", taskid="default"),
]

inproduct = [
    Duty(date=date(2025, 2, 23), employee="余行方", type="in_product", taskid="default"),
    Duty(date=date(2025, 2, 22), employee="包云飞", type="in_product", taskid="default"),
    Duty(date=date(2025, 2, 22), employee="沈毅", type="in_product", taskid="default"),
    Duty(date=date(2025, 2, 23), employee="蒋炯明", type="in_product", taskid="default"),
    Duty(date=date(2025, 3, 22), employee="张南", type="in_product", taskid="default"),
    Duty(date=date(2025, 3, 22), employee="徐蒲金", type="in_product", taskid="default"),
    Duty(date=date(2025, 3, 23), employee="秦刚", type="in_product", taskid="default"),
    Duty(date=date(2025, 3, 23), employee="王仲晖", type="in_product", taskid="default"),
]

wait_to_process = inproduct + weekend
for duty in wait_to_process:
    session.merge(duty)
    session.commit()

inproducts = [
    DutyCalendar(date=date(2025,5,24), type="in_product", maintainer="system"),
    DutyCalendar(date=date(2025,5,25), type="in_product", maintainer="system")
]
for duty in inproducts:
    session.merge(duty)
    session.commit()