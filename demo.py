from datetime import date, timedelta
from sqlalchemy import select
from components import session
from components.dbmodel import DutyCalendar, Duty, HolidayCalendar
from ortools.sat.python import cp_model


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
                                                HolidayCalendar.date.between(when_start, when_end))
        records = session.execute(sqlstmt).scalars().all()
        holidays = [record.date for record in records]
        holidays = list(set(holidays) - set(self.inproduct_days))
        holidays.sort()

        return holidays

    def _generate_all_working_date(self):
        all_days = [(when_start + timedelta(days=i)) for i in range((self.end - self.start).days + 1)]
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

    def schedule(self):
        total_a_inproduct, group_a_inproduct = self.get_members("A", "in_product")
        total_a_holiday, group_a_holiday = self.get_members("A", "uat-weekend")
        group_a = self.merge_group(group_a_inproduct, group_a_holiday)
        total_a = total_a_inproduct + total_a_holiday

        total_b_inproduct, group_b_inproduct = self.get_members("B", "in_product")
        total_b_holiday, group_b_holiday = self.get_members("B", "uat-weekend")
        group_b = self.merge_group(group_b_inproduct, group_b_holiday)
        total_b = total_b_holiday + total_b_inproduct

        _, group_c = self.get_members("C", "uat-weekend")
        all_employees = group_a + group_b + group_c
        num_of_employees = len(all_employees)
        person_index = {p: i for i, p in enumerate(all_employees)}
        days_in_period = (self.end - self.start).days + 1
        model = cp_model.CpModel()

        # 设置模型变量： 每个值班人员每一天的工作状态{0: 休假, 1: 工作}
        vacation = dict()
        for e in range(num_of_employees):
            for s in range(3):
                for d in range(days_in_period):
                    vacation[(e, s, d)] = model.NewBoolVar(f"{e}_shift_{s}_day_{d}")

        # 约束1 优先安排投产值班
        inproduct_days = [(day - self.start).days for day in self.shiftcalendar.get_days("in_product")]
        for d in inproduct_days:
            if (self.start + timedelta(days=d)).weekday() == 5:
                model.Add(sum(vacation[(person_index[e], 0, d)]
                              for e in group_a_inproduct) == 2)
            if (self.start + timedelta(days=d)).weekday() == 6:
                model.Add(sum(vacation[(person_index[e], 0, d)]
                              for e in group_a_inproduct) == 1)
                model.Add(sum(vacation[(person_index[e], 0, d)]
                              for e in group_b_inproduct) == 1)

        # 约束2 安排双休日值班
        weekend_days = [(day - self.start).days for day in self.shiftcalendar.get_days("uat-weekend")]
        for d in weekend_days:
            model.Add(sum(vacation[(person_index[e], 1, d)]
                          for e in group_a) == 1)
            if (self.start + timedelta(days=d)).weekday() == 5:
                model.Add(sum(vacation[(person_index[e], 1, d)]
                              for e in group_b) == 1)
            elif (self.start + timedelta(days=d)).weekday() == 6:
                model.Add(sum(vacation[(person_index[e], 1, d)]
                              for e in group_c) == 1)
            else:
                model.Add(sum(vacation[(person_index[e], 1, d)]
                              for e in (group_c + group_b)) == 1)

        # 约束3 安排工作日值班
        working_days = [(day - self.start).days for day in self.shiftcalendar.get_days("uat-night")]
        for d in working_days:
            model.Add(sum(vacation[(person_index[e], 2, d)]
                          for e in group_a) == 1)

        # 约束 每人每天只参加一种类型的值班
        for e in all_employees:
            for d in range(days_in_period):
                model.AddExactlyOne(vacation[person_index[e], s, d] for s in range(3))

        # 约束4 投产值班人员值班次数公平分配
        avg = total_a_inproduct // len(group_a_inproduct)
        for e in group_a_inproduct:
            total = sum(vacation[(person_index[e], 0, d)] for d in inproduct_days)
            model.Add(total >= avg)
            model.Add(total <= avg + 1)

        avg = total_a // len(group_a)
        spdays = inproduct_days + weekend_days
        for e in group_a:
            condition = sum(vacation[(person_index[e], s, d)] for s in range(2) for d in spdays)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 1)

        avg = (total_a + len(working_days))// len(group_a)
        spdays = inproduct_days + weekend_days + working_days
        for e in group_a:
            condition = sum(vacation[(person_index[e], s, d)] for s in range(2) for d in spdays)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 1)

        spdays = inproduct_days + weekend_days
        avg = len(spdays) // len(group_b + group_c)
        for e in (group_b + group_c):
            condition = sum(vacation[(person_index[e], s, d)] for s in range(3) for d in spdays)
            model.Add(condition >= avg)
            model.Add(condition <= avg + 2)


        # 求解
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for e in range(num_of_employees):
                print(f"Employee {all_employees[e]}: ", end="")
                for d in range(days_in_period):
                    # print(f"{solver.Value(vacation[(e, 2, d)])} ", end="")
                    print(f"{solver.Value(induty[e, d])} ", end="")
                print()
        else:
            print("No solution found!")

    def get_members(self, group_name: str, duty_type: str):
        """ 获取本轮值班人员
        依据各类型的值班天数，值班人员池，生成本轮值班的人员清单。
        :param group_name: 组类型
        :param duty_type: 值班类型
        :return: 总人次，参与本轮值班的人员列表
        """
        dutydays = self.shiftcalendar.get_days(duty_type)
        group = list()
        if group_name == "A":
            employees = A_group
        elif group_name == "B":
            employees = B_group
        elif group_name == "C":
            employees = C_group
        else:
            employees = []

        if dutydays:
            additions = list()
            for employee in employees:
                sqlstmt = select(Duty).where(Duty.employee == employee,
                                             Duty.type == duty_type).order_by(Duty.date.desc())
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
        从target中剔除origin，按照顺序合并二组
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



# 定义三个组的成员
A_group = ["陈雪莲", "邱凌", "卓燕斌", "万米",
           "包云飞", "沈毅", "蒋炯明", "王仲晖",
           "徐蒲金", "秦刚", "胡继云", "刘敏",
           "郭天赐", "孙俊敏", "陈栋"]
B_group = ["张南", "徐升", "余行方"]
C_group = ["祁玉权", "何超超"]


when_start = date(2025, 3, 1)
when_end = date(2025, 6, 1)

shift_calendar = ShiftCalendar(when_start, when_end)
print("投产值班日：")
print(shift_calendar.inproduct_days)
print("节假日：")
print(shift_calendar.holidays)

abc = ApplicationRuleNormal(when_start, when_end)
abc.schedule()

