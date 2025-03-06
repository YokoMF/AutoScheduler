from abc import ABC, abstractmethod
from datetime import date
import calendar
from sqlalchemy import select
from components import session
from components.dbmodel import Duty

class Report(ABC):
    @abstractmethod
    def display(self):
        pass

    @abstractmethod
    def export(self):
        pass

class DutyReport(Report):
    def __init__(self, year, month):
        self.year = year
        self.month = month

    def display(self):
        _, days_in_month = calendar.monthrange(self.year, self.month)
        print(f"{self.year}年{self.month}月值班表：")
        rows = self.generate_report_rows()
        for d in range(1, days_in_month + 1):
            print(f"|{self.year}-{self.month}-{d}".ljust(10), end="|")
            for row in rows:
                if row.date != date(self.year, self.month, d):
                    continue
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


    def export(self):
        print("DutyReport export")

    def generate_report_rows(self):
        _, days_in_month = calendar.monthrange(self.year, self.month)
        start = date(self.year, self.month, 1)
        end = date(self.year, self.month, days_in_month)
        stmt = select(Duty).where(Duty.date.between(start, end))
        rows = session.execute(stmt).scalars().all()

        return rows if rows else list()
