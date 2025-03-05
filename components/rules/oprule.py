from abc import ABC, abstractmethod
import calendar
import datetime
from collections import namedtuple
import yaml
from ortools.sat.python import cp_model
from sqlalchemy import select, func
from components.dbmodel import HolidayCalendar
from components import session


CommonParameter = namedtuple("CommonParameter",
                             "name description members holidays "
                             "max_vacation_days spring labor national extra")

with open(r"./conf/parameter.yaml", "r", encoding="utf-8") as file:
    PARAMETERS = yaml.safe_load(file)

stmt = select(func.max(HolidayCalendar.date)).where(HolidayCalendar.holiday == 2)
Month_Of_Spring = session.execute(stmt).scalar()


class OperationRule(ABC):

    @abstractmethod
    def schedule(self, *args, **kwargs):
        pass

    @abstractmethod
    def demo(self):
        pass

    @abstractmethod
    def dump_to_excel(self):
        pass


class OperationRuleOne(OperationRule):
    def __init__(self, seq: int):
        self.parameter = CommonParameter(**PARAMETERS["operation"]["OperationRuleOne"][seq])

    def schedule(self, year: int, month: int):
        # 定义模型
        model = cp_model.CpModel()

        # 模型参数
        if month == 5:
            max_vacation_days = self.parameter.labor
        elif month == 10:
            max_vacation_days = self.parameter.national
        elif month == Month_Of_Spring:
            max_vacation_days = self.parameter.spring
        else:
            max_vacation_days = self.parameter.max_vacation_days

        num_of_employees = len(self.parameter.members)
        _, days_in_month = calendar.monthrange(year, month)
        all_weekdays = [datetime.date(year, month, d).weekday()
                    for d in range(1, days_in_month + 1)]

        # 设置模型变量： 每个值班人员每一天的工作状态{0: 工作, 1: 休假}
        vacation = dict()
        for e in range(num_of_employees):
            for d in range(days_in_month):
                vacation[(e, d)] = model.NewBoolVar(f"{e}_day_{d}")

        # 约束1 每个人每个月最多休假 max_vacation_days 天
        for e in range(num_of_employees):
            model.Add(sum(vacation[(e, d)]
                          for d in range(days_in_month)) == max_vacation_days)

        # 约束2 固定休假
        balance = datetime.date(year, month, 1).weekday()
        for e in range(num_of_employees):
            for d in range(days_in_month):
                if datetime.date(year, month, d).weekday() in self.parameter.holidays:
                    model.Add(vacation[(e, d)] == 1)

        # 约束3 优先选择补休
        rest_days = max_vacation_days
        for i in range(self.parameter.holidays):
            rest_days = rest_days - all_weekdays.count(i)

        if rest_days <= all_weekdays.count(self.parameter.extra):
            for e in range(num_of_employees):
                model.Add(sum(vacation[(e, d)]
                              for d in range(days_in_month)
                              if datetime.date(year, month, d).weekday() in self.parameter.holidays) == rest_days)
        else:
            for e in range(num_of_employees):
                model.Add(sum(vacation[(e, d)]
                              for d in range(days_in_month)
                              if datetime.date(year, month, d).weekday() in self.parameter.holidays) == all_weekdays.count(self.parameter.extra))

        # 定义目标函数：尽量避免两人同时在extra日期同时休息
        all_extra_days = [d - 1 for d in range(1, days_in_month + 1)
                          if datetime.date(year, month, d).weekday() == self.parameter.extra]
        violation = {}
        for d in all_extra_days:
            violation[d] = model.NewBoolVar(f"violation_{d}")
            model.Add(sum(vacation[(e, d)] for e in range(num_of_employees)) < num_of_employees).OnlyEnforceIf(violation[d].Not())
            model.Add(sum(vacation[(e, d)] for e in range(num_of_employees)) == num_of_employees).OnlyEnforceIf(violation[d])

        # 定义目标函数
        model.Minimize(sum(violation[d] for d in all_extra_days))

        # 求解
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
