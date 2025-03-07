import uuid
import calendar
import datetime
import logging
from collections import namedtuple
import yaml
from ortools.sat.python import cp_model
from sqlalchemy import select, func
from components.dbmodel import HolidayCalendar, Duty, TaskId
from components import session

logger = logging.getLogger("AS")
with open(r"./conf/parameter.yaml", "r", encoding="utf-8") as file:
    PARAMETERS = yaml.safe_load(file)

stmt = select(func.max(HolidayCalendar.date)).where(HolidayCalendar.holiday == 2)
last_day_of_spring = session.execute(stmt).scalar()
Month_Of_Spring = last_day_of_spring.month


class OperationRule:
    def __init__(self, year, month, rule):
        self.type = rule
        self.year = year
        self.month = month
        self.status = None
        self.parameter = None
        self.vacation = None
        self.solver = None
        self.uuid = uuid.uuid4().hex

    def schedule(self, *args, **kwargs):
        raise NotImplementedError("schedule method must be implemented!")

    def demo(self):
        logger.info(f"开始演示{self.parameter["name"]}排班结果")
        members = self.parameter["members"]
        _, days_in_month = calendar.monthrange(self.year, self.month)
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            for e in range(len(members)):
                print(f"Employee {members[e]}: ", end="")
                for d in range(1, days_in_month + 1):
                    print(f"{self.solver.Value(self.vacation[(e, d)])} ", end="")
                print()
        else:
            logger.error(f"{self.parameter["name"]} No solution found!")

    def dump_to_excel(self):
        raise NotImplementedError("dump_to_excel method must be implemented!")

    def commit(self):
        logger.info(f"{self.parameter["name"]}-{self.uuid}: start committing schedule...")
        members = self.parameter["members"]
        _, days_in_month = calendar.monthrange(self.year, self.month)
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            task = TaskId(uuid=self.uuid, created_timestamp=datetime.datetime.now(), status="Pending")
            session.merge(task)
            session.commit()
            logger.info(f"{self.parameter["name"]}-{self.uuid}:  commit pending.")
            for e in range(len(members)):
                for d in range(1, days_in_month + 1):
                    if not self.solver.Value(self.vacation[(e, d)]):
                        duty = Duty(date=datetime.date(self.year, self.month, d),
                                    employee=members[e],
                                    type=self.type,
                                    taskid=self.uuid)
                        logger.debug(f"{duty.date}, {duty.type}, {duty.employee}, {duty.taskid}")
                        session.merge(duty)
                        session.commit()
                task.status = "completed"
                session.merge(task)
            logger.info(f"{self.parameter["name"]}-{self.uuid}:  commit complete.")
        else:
            logger.error(f"{self.parameter["name"]}-{self.uuid}: No solution found!")


class OperationRuleDay(OperationRule):
    def __init__(self, seq: int, year: int, month: int):
        super().__init__(year, month,"OperationRuleDay")
        self.parameter = PARAMETERS["operation"][self.type][seq]

    def schedule(self):
        # 定义模型
        model = cp_model.CpModel()
        month = self.month
        year = self.year

        # 模型参数
        if month == 5:
            max_vacation_days = self.parameter["labor"]
        elif month == 10:
            max_vacation_days = self.parameter["national"]
        elif month == Month_Of_Spring:
            max_vacation_days = self.parameter["spring"]
        else:
            max_vacation_days = self.parameter["max_vacation_days"]

        num_of_employees = len(self.parameter["members"])
        _, num_of_days = calendar.monthrange(year, month)
        days_in_month = [d for d in range(1, num_of_days + 1)]
        all_weekdays = [datetime.date(year, month, d).weekday()
                    for d in days_in_month]

        # 设置模型变量： 每个值班人员每一天的工作状态{0: 工作, 1: 休假}
        vacation = dict()
        for e in range(num_of_employees):
            for d in days_in_month:
                vacation[(e, d)] = model.NewBoolVar(f"{e}_day_{d}")

        # 约束1 每个人每个月最多休假 max_vacation_days 天
        for e in range(num_of_employees):
            model.Add(sum(vacation[(e, d)]
                          for d in days_in_month) == max_vacation_days)

        # 约束2 固定休假
        for e in range(num_of_employees):
            for d in days_in_month:
                if datetime.date(year, month, d).weekday() in self.parameter["holidays"]:
                    model.Add(vacation[(e, d)] == 1)

        # 约束3 优先选择补休
        rest_days = max_vacation_days
        for i in self.parameter["holidays"]:
            rest_days = rest_days - all_weekdays.count(i)

        if rest_days <= all_weekdays.count(self.parameter["extra"]):
            for e in range(num_of_employees):
                model.Add(sum(vacation[(e, d)]
                              for d in days_in_month
                              if datetime.date(year, month, d).weekday() == self.parameter["extra"]) == rest_days)
        else:
            for e in range(num_of_employees):
                model.Add(sum(vacation[(e, d)]
                              for d in days_in_month
                              if datetime.date(year, month, d).weekday() == self.parameter["extra"]) == all_weekdays.count(self.parameter["extra"]))

        # 定义目标函数：尽量避免两人同时在extra日期同时休息
        all_extra_days = [d for d in days_in_month
                          if datetime.date(year, month, d).weekday() == self.parameter["extra"]]
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

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            self.status = status
            self.solver = solver
            self.vacation = vacation
            logger.info(f"{self.parameter["name"]} Solution found!")
        else:
            self.status = "failed"

    def dump_to_excel(self):
        pass


class OperationRuleBase(OperationRule):
    def __init__(self, seq: int, year: int, month: int):
        super().__init__(year, month, "OperationRuleBase")
        self.parameter = PARAMETERS["operation"][self.type][seq]

    def schedule(self):
        model = cp_model.CpModel()
        month = self.month
        year = self.year
        _, num_of_days = calendar.monthrange(year, month)
        num_of_employees = len(self.parameter["members"])

        begin = datetime.date(self.year, self.month, 1)
        end = datetime.date(self.year, self.month, num_of_days)
        sqlstmt = (select(HolidayCalendar).filter(HolidayCalendar.holiday != 0)
                   .filter(HolidayCalendar.date.between(begin, end)))
        rows = session.execute(sqlstmt).scalars().all()
        holidays = [row.date.day for row in rows]
        days_in_month = [d for d in range(1, num_of_days + 1)]

        # 模型变量
        vacation = dict()
        for e in range(num_of_employees):
            for d in days_in_month:
                vacation[(e, d)] = model.NewBoolVar(f"{e}_day_{d}")

        for e in range(num_of_employees):
            for d in holidays:
                model.Add(vacation[(e, d)] == 1)

        # 求解
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            self.status = status
            self.solver = solver
            self.vacation = vacation
            logger.info(f"{self.parameter["name"]} Solution found!")
        else:
            self.status = "failed"


    def dump_to_excel(self):
        pass
    


class OperationRuleNight(OperationRule):
    def __init__(self, seq: int, year: int, month: int):
        super().__init__(year, month, "OperationRuleNight")
        self.parameter = PARAMETERS["operation"][self.type][seq]
        self.interval = 3

    def schedule(self):
        model = cp_model.CpModel()
        month = self.month
        year = self.year
        _, num_of_days = calendar.monthrange(year, month)
        days_in_month = [d for d in range(1, num_of_days + 1)]
        num_of_employees = len(self.parameter["members"])

        if not self.parameter["base_date"]:
            sqlstmt = select(func.max(Duty.date)).where(Duty.employee == self.parameter["members"][0]["name"])
            basedate = session.execute(sqlstmt).scalar()
        else:
            basedate = datetime.datetime.strptime(self.parameter["base_date"], "%Y-%m-%d").date()
        start = self.get_first_working_day(basedate)
        working_days = [d for d in range(start.day, num_of_days + 1, 3)]
        holidays = list(set(days_in_month) - set(working_days))

        vacation = dict()
        for e in range(num_of_employees):
            for d in days_in_month:
                vacation[(e, d)] = model.NewBoolVar(f"{e}_day_{d}")

        for e in range(num_of_employees):
            for d in holidays:
                model.Add(vacation[(e, d)] == 1)
            for d in working_days:
                model.Add(vacation[(e, d)] == 0)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            self.status = status
            self.solver = solver
            self.vacation = vacation
            logger.info(f"{self.parameter["name"]} Solution found!")
        else:
            self.status = "failed"

    def dump_to_excel(self):
        pass

    def get_first_working_day(self, srcdate: datetime.date):
        first_day_of_month = datetime.date(self.year, self.month, 1)
        if srcdate > first_day_of_month:
            raise ValueError("基础日期大于排班日期")

        current = srcdate
        while current.month <= self.month:
            if current >= first_day_of_month:
                return current

            current += datetime.timedelta(days=self.interval)

        return None


class OperationRuleMiddle(OperationRule):
    def __init__(self, seq: int, year: int, month: int):
        super().__init__(year, month, "OperationRuleMiddle")
        self.parameter = PARAMETERS["operation"][self.type][seq]


    def schedule(self):
        _, num_of_days = calendar.monthrange(self.year, self.month)
        Member = namedtuple("Member", "name workdays")
        members = [Member(m["name"], m["workdays"]) for m in self.parameter["members"]]
        num_of_employees = len(members)
        days_in_month = [d for d in range(1, num_of_days + 1)]
        start = datetime.date(self.year, self.month, 1)
        end = datetime.date(self.year, self.month, num_of_days)

        vacation = {}
        for e in range(num_of_employees):
            sqlstmt = select(Duty).where(Duty.employee == members[e].name
                                         and Duty.date.between(start, end))
            rows = session.execute(sqlstmt).scalars().all()
            workdays = [row.date for row in rows]
            for d in days_in_month:
                day = datetime.date(self.year, self.month, d)
                if day in workdays and day.weekday() in members[e].workdays:
                    vacation[(e, d)] = 0
                else:
                    vacation[(e, d)] = 1

        self.vacation = vacation
        self.status = "success"

    def demo(self):
        logger.info("开始演示中班排班结果。请先完成夜班排班！")
        _, num_of_days = calendar.monthrange(self.year, self.month)
        Member = namedtuple("Member", "name workdays")
        members = [Member(m["name"], m["workdays"]) for m in self.parameter["members"]]
        days_in_month = [d for d in range(1, num_of_days + 1)]

        for e in range(len(members)):
            print(f"Employee {members[e].name}: ", end="")
            for d in days_in_month:
                print(f"{self.vacation[e, d]} ", end="")
            print()

    def dump_to_excel(self):
        pass

    def commit(self):
        logger.info(f"{self.parameter["name"]}-{self.uuid}: start committing schedule...")
        members = self.parameter["members"]
        _, days_in_month = calendar.monthrange(self.year, self.month)
        if self.status == "success":
            task = TaskId(uuid=self.uuid, created_timestamp=datetime.datetime.now(), status="Pending")
            session.merge(task)
            session.commit()
            logger.info(f"{self.parameter["name"]}-{self.uuid}:  commit pending.")
            for e in range(len(members)):
                for d in range(1, days_in_month + 1):
                    if not self.vacation[(e, d)]:
                        duty = Duty(date=datetime.date(self.year, self.month, d),
                                    employee=members[e]["name"],
                                    type=self.type,
                                    taskid=self.uuid)
                        logger.debug(f"{duty.date}, {duty.type}, {duty.employee}, {duty.taskid}")
                        session.merge(duty)
                        session.commit()
                task.status = "completed"
                session.merge(task)
            logger.info(f"{self.parameter["name"]}-{self.uuid}:  commit complete.")
        else:
            logger.error(f"{self.uuid}: No solution found!")
