from datetime import date
from components.rules.uatshift import ShiftCalendar, ApplicationRuleNormal

when_start = date(2025, 4, 1)
when_end = date(2025, 6, 1)

shift_calendar = ShiftCalendar(when_start, when_end)
print("投产值班日：")
print(shift_calendar.inproduct_days)
print("节假日：")
print(shift_calendar.holidays)

abc = ApplicationRuleNormal(when_start, when_end)
abc.schedule()
abc.demo()