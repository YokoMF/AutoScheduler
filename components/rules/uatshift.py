from datetime import date, timedelta
import logging
import yaml
import uuid
from sqlalchemy import select
from components import session
from components.dbmodel import DutyCalendar, Duty, HolidayCalendar
from ortools.sat.python import cp_model

logger = logging.getLogger("AS")
with open(r"./conf/parameter.yaml", "r", encoding="utf-8") as file:
    PARAMETERS = yaml.safe_load(file)

class ShiftCalendar:
    def __init__(self, start: date, end: date):
        self.start = start
        self.end = end
        self.inproduct_days = self._generate_all_inproduct_date()
        self.holidays = self._generate_all_holidays_date()
        self.working_days = self._generate_all_working_date()

    def _generate_all_inproduct_date(self):
        # 确认投产值班的天数
        sqlstmt = select(DutyCalendar).where(DutyCalendar.type == "in_product",
                                             DutyCalendar.date.between(self.start, self.end))
        records = session.execute(sqlstmt).scalars().all()
        inproduct_days = [record.date for record in records]

        return inproduct_days

    def _generate_all_holidays_date(self):
        # 确认双休日的值班天数
        sqlstmt = select(HolidayCalendar).where(HolidayCalendar.holiday != 0,
                                                HolidayCalendar.date.between(self.start, self.end))
        records = session.execute(sqlstmt).scalars().all()
        holidays = [record.date for record in records]
        holidays = list(set(holidays) - set(self.inproduct_days))
        holidays.sort()

        return holidays

    def _generate_all_working_date(self):
        all_days = [(self.start + timedelta(days=i)) for i in range((self.end - self.start).days + 1)]
        working_days = list(set(all_days) - set(self.holidays) - set(self.inproduct_days))
        working_days.sort()

        return working_days

    def get_days(self, duty_type: str):
        if duty_type == "in_product":
            return self.inproduct_days
        elif duty_type == "uat-weekend":
            return self.holidays
        elif duty_type == "uat-night":
            return self.working_days
        else:
            return []


class ApplicationRuleNormal:
    def __init__(self, start: date, end: date):
        self.start = start
        self.end = end
        self.shiftcalendar = ShiftCalendar(start, end)
        self.parameter = PARAMETERS["uatgroup"]["UatShiftRule"]
        self.status = None
        self.vacation = None
        self.solver = None
        self.uuid = uuid.uuid4().hex
        self.num_of_employees = 0
        self.all_employees = []

    def schedule(self):
        total_a_inproduct, group_a_inproduct = self.get_members("A", "in_product")
        total_a_holiday, group_a_holiday = self.get_members("A", "uat-weekend")
        group_a = self.merge_group(group_a_inproduct, group_a_holiday)
        total_a = total_a_inproduct + total_a_holiday

        total_b_inproduct, group_b_inproduct = self.get_members("B", "in_product")
        total_b_holiday, group_b_holiday = self.get_members("B", "uat-weekend")
        group_b = self.merge_group(group_b_inproduct, group_b_holiday)

        _, group_c = self.get_members("C", "uat-weekend")
        all_employees = group_a + group_b + group_c
        self.all_employees = all_employees
        num_of_employees = len(all_employees)
        self.num_of_employees = num_of_employees
        person_index = {p: i for i, p in enumerate(all_employees)}
        days_in_period = (self.end - self.start).days + 1
        model = cp_model.CpModel()

        # 设置模型变量： 每个值班人员每一天的工作状态{0: 休假, 1: 工作}
        vacation = dict()
        for e in range(num_of_employees):
            for d in range(days_in_period):
                vacation[(e, d)] = model.NewBoolVar(f"{e}_day_{d}")

        inproduct_days = [(day - self.start).days for day in self.shiftcalendar.get_days("in_product")]
        weekend_days = [(day - self.start).days for day in self.shiftcalendar.get_days("uat-weekend")]
        working_days = [(day - self.start).days for day in self.shiftcalendar.get_days("uat-night")]

        # 约束1 优先安排投产值班
        for d in inproduct_days:
            if (self.start + timedelta(days=d)).weekday() == 5:
                model.Add(sum(vacation[(person_index[e], d)]
                              for e in group_a_inproduct) == 2)
                model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_c)
            if (self.start + timedelta(days=d)).weekday() == 6:
                model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_a_inproduct)
                model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_b_inproduct)
            model.Add(sum(vacation[person_index[e], d] for e in all_employees) == 2)

        # 约束2 安排双休日值班
        for d in weekend_days:
            model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_a)
            if (self.start + timedelta(days=d)).weekday() == 5:
                model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_b)
            elif (self.start + timedelta(days=d)).weekday() == 6:
                model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_c)
            else:
                model.AddExactlyOne(vacation[(person_index[e], d)] for e in (group_c + group_b))

        # 约束3 安排工作日值班
        for d in working_days:
            model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_a)

        # 约束4 投产值班人员值班次数公平分配
        if len(group_a_inproduct):
            avg = total_a_inproduct // len(group_a_inproduct)
            for e in group_a_inproduct:
                total = sum(vacation[(person_index[e], d)] for d in inproduct_days)
                model.Add(total >= avg)
                model.Add(total <= avg + 1)

        # 双休日开放平均
        avg = total_a // len(group_a)
        spdays = inproduct_days + weekend_days
        for e in group_a:
            condition = sum(vacation[(person_index[e], d)] for d in spdays)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 1)

        # 工作日开放平均
        avg = len(working_days) // len(group_a)
        for e in group_a:
            condition = sum(vacation[person_index[e], d] for d in working_days)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 1)

        # 主机双休日平均
        mf_days = [d for d in weekend_days if (self.start + timedelta(days=d)).weekday() == 5]
        avg = len(mf_days) // len(group_b)
        for e in group_b:
            condition = sum(vacation[person_index[e], d] for d in mf_days)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 1)

        mf_days = [d for d in weekend_days if (self.start + timedelta(days=d)).weekday() == 6]
        avg = len(mf_days) // len(group_c)
        for e in group_c:
            condition = sum(vacation[person_index[e], d] for d in mf_days)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 1)

        # 开放值班投产及节假日值班间隔保证
        spdays = weekend_days + inproduct_days
        spdays.sort()
        interval = len(group_a) - 4
        for e in group_a:
            for d in range(len(spdays) - interval):
                model.Add(sum(vacation[(person_index[e], spdays[d + i])] for i in range(interval + 1)) <= 1)

        # 开放夜间值班间隔保证
        spdays = working_days
        spdays.sort()
        interval = 13
        for e in group_a:
            for d in range(len(spdays) - interval):
                model.Add(sum(vacation[(person_index[e], spdays[d + i])] for i in range(interval + 1)) <= 1)

        # 开放值班间隔保证
        spdays = weekend_days + inproduct_days + working_days
        spdays.sort()
        interval = 7
        for e in group_a:
            for d in range(len(spdays) - interval):
                model.Add(sum(vacation[(person_index[e], spdays[d + i])] for i in range(interval + 1)) <= 1)

        # 主机外员值班节假日间隔保证
        spdays = weekend_days
        interval = len(group_c) - 1
        spdays = [d for d in spdays if (self.start + timedelta(days=d)).weekday() != 5]
        spdays += [d for d in inproduct_days  if (self.start + timedelta(days=d)).weekday() == 5]
        spdays.sort()
        for e in group_c:
            for d in range(len(spdays) - interval):
                model.Add(sum(vacation[(person_index[e], spdays[d + i])] for i in range(interval + 1)) <= 1)

        # 主机自有员工值班节假日间隔保证
        spdays = weekend_days
        spdays = [d for d in spdays if (self.start + timedelta(days=d)).weekday() != 6]
        spdays += [d for d in inproduct_days if (self.start + timedelta(days=d)).weekday() != 5]
        spdays.sort()
        interval = len(group_b) - 1
        for e in group_b:
            for d in range(len(spdays) - interval):
                model.Add(sum(vacation[(person_index[e], spdays[d + i])] for i in range(interval + 1)) <= 1)


        # 求解
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            self.status = status
            self.solver = solver
            self.vacation = vacation
            logger.info("UatShiftRule Solution found!")
        else:
            self.status = "failed"

    def demo(self):
        days_in_period = (self.end - self.start).days + 1
        if self.status == cp_model.OPTIMAL or self.status == cp_model.FEASIBLE:
            for e in range(self.num_of_employees):
                print(f"Employee {self.all_employees[e]}: ", end="")
                for d in range(days_in_period):
                    print(f"{self.solver.Value(self.vacation[(e, d)])} ", end="")
                print()
        else:
            print("No solution found!")

    def get_members(self, group_name: str, duty_type: str):
        """ 获取本轮值班人员
        依据各类型的值班天数，值班人员池，计算并生成本轮值班的人员清单。
        :param group_name: 组类型
        :param duty_type: 值班类型
        :return: 总人次，参与本轮值班的人员列表
        """
        dutydays = self.shiftcalendar.get_days(duty_type)
        group = list()
        if group_name == "A":
            employees = self.parameter[0]["members"]
        elif group_name == "B":
            employees = self.parameter[1]["members"]
        elif group_name == "C":
            employees = self.parameter[2]["members"]
        else:
            employees = []

        if dutydays:
            additions = list()
            for employee in employees:
                sqlstmt = select(Duty).where(Duty.employee == employee,
                                             Duty.type == duty_type,
                                             Duty.date < self.start).order_by(Duty.date.desc())
                records = session.execute(sqlstmt).scalars().all()
                if records:
                    additions.append(records[0])
                else:
                    group.append(employee)
            if additions:
                additions = sorted(additions, key=lambda duty: duty.date)
                group = group + [e.employee for e in additions]

        if duty_type == "in_product" and group_name == "A":
            total = 0
            for dutyday in dutydays:
                if dutyday.weekday() == 5:
                    total += 2
                else:
                    total += 1
        elif duty_type == "in_product" and group_name == "B":
            total = 0
            for dutyday in dutydays:
                if dutyday.weekday() == 6:
                    total += 1
        else:
            total = len(dutydays)

        return total, group[:total]

    @staticmethod
    def merge_group(origin: list, target: list):
        """合并组
        从target中剔除origin，按照顺序合并二组，返回合并后的组。该方法用于生成参与投产和节假日值班的人员的顺序。
        :param origin:
        :param target:
        :return:
        """
        final_team = []
        for person in target:
            if person not in origin:
                final_team.append(person)
        final_team += origin

        return final_team
