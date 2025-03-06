import datetime
import calendar
from sqlalchemy import select
from components.rules.operation import (OperationRuleDay,
                                        OperationRuleBase,
                                        OperationRuleNight,
                                        OperationRuleMiddle,
                                        PARAMETERS)
from components.dbmodel import Duty
from components import session

for rule_name in PARAMETERS["operation"]:
    for i in range(len(PARAMETERS["operation"][rule_name])):
        rule = eval(f"{rule_name}")(i, 2025, 4)
        rule.schedule()
        rule.commit()

_, days_in_month = calendar.monthrange(2025, 4)
for d in range(1, days_in_month):
    stmt = select(Duty).where(Duty.date == datetime.date(2025, 4, d))
    rows = session.execute(stmt).scalars().all()
    print(f"|2025-4-{d}".ljust(10), end="|")
    for row in rows:
        if row.type == "OperationRuleMiddle":
            print(f"{row.employee}(中,夜)".ljust(12), end="|")
        elif row.type == "OperationRuleNight":
            ignore = False
            for item in rows:
                if (item.type == "OperationRuleMiddle"
                        and item.employee == row.employee
                        and row.date == item.date):
                    ignore = True
                    break
            if not ignore:
                print(f"{row.employee}(夜)".ljust(12), end="|")
        else:
            print(f"{row.employee}".ljust(12), end="|")
    print()
