from ortools.sat.python import cp_model
import calendar
import datetime
from sqlalchemy import select
from components.dbmodel import DutyCalendar
from components import session

# 定义三个组的成员
A_group = ["陈雪莲", "邱凌", "卓燕斌", "万米",
           "包云飞", "沈毅", "蒋炯明", "王仲晖",
           "徐蒲金", "秦刚", "胡继云", "刘敏",
           "郭天赐", "孙俊敏", "陈栋"]
B_group = ["张南", "徐升", "余行方"]
C_group = ["祁玉权", "何超超"]

employees = A_group + B_group + C_group
num_of_employees = len(employees)
num_shifts = 3  # 三个班次
year = 2025
month = 3
_, num_of_days = calendar.monthrange(year, month)
days_in_month = [d for d in range(1, num_of_days + 1)]
all_weekdays = [datetime.date(year, month, d).weekday()
                for d in days_in_month]

# 构建投产值班表
start = datetime.date(year, month, 1)
end = datetime.date(year, month, num_of_days)
stmt = select(DutyCalendar).where(DutyCalendar.type == "投产"
                                  and
                                  DutyCalendar.date.between(start, end))
rows = session.execute(stmt).scalars().all()
inproduct_dates = [row.date for row in rows]

# 构建索引映射
person_index = {p: i for i, p in enumerate(employees)}

# 创建模型
model = cp_model.CpModel()

# 定义变量 schedule[d, s, p]，表示第 d 天，第 s 班次，第 p 人员是否值班
schedule = {}
for d in days_in_month:
    for s in range(num_shifts):
        for p in range(num_of_employees):
            schedule[d, s, p] = model.NewBoolVar(f"schedule_{d}_{s}_{p}")

# 添加值班规则
for d in days_in_month:
    # 班次 1: 双休日投产值班
    current = datetime.date(year, month, d)
    if current in inproduct_dates:  # 周六 (5), 周日 (6)
        if current.weekday() == 5:  # 周六: A 组 2 人
            model.Add(sum(schedule[d, 0, person_index[p]] for p in A_group) == 2)
        else:  # 周日: A 组 1 人, B 组 1 人
            model.Add(sum(schedule[d, 0, person_index[p]] for p in A_group) == 1)
            model.Add(sum(schedule[d, 0, person_index[p]] for p in B_group) == 1)

    print("jo")

    # 班次 2: 普通双休日值班
    if weekday in [5, 6]:
        if weekday == 5:  # 周六: A 组 1 人, B 组 1 人
            model.Add(sum(schedule[d, 1, person_index[p]] for p in A_group) == 1)
            model.Add(sum(schedule[d, 1, person_index[p]] for p in B_group) == 1)
        else:  # 周日: A 组 1 人, C 组 1 人
            model.Add(sum(schedule[d, 1, person_index[p]] for p in A_group) == 1)
            model.Add(sum(schedule[d, 1, person_index[p]] for p in C_group) == 1)

    # 班次 3: 工作日 A 组 1 人
    if weekday in range(5):  # 周一到周五
        model.Add(sum(schedule[d, 2, person_index[p]] for p in A_group) == 1)

# 组内公平分配值班
for group in [A_group, B_group, C_group]:
    min_shifts = (num_days * num_shifts) // len(group)
    max_shifts = min_shifts + 1
    for p in group:
        total_shifts = sum(schedule[d, s, person_index[p]] for d in range(num_days) for s in range(num_shifts))
        model.Add(total_shifts >= min_shifts)
        model.Add(total_shifts <= max_shifts)

# 避免连续值班（两次值班间隔尽可能长）
for p in all_people:
    for d in range(num_days - 1):
        model.Add(sum(schedule[d, s, person_index[p]] for s in range(num_shifts)) +
                  sum(schedule[d + 1, s, person_index[p]] for s in range(num_shifts)) <= 1)

# 目标函数：最小化值班次数不均衡
model.Minimize(sum(schedule[d, s, p] for d in range(num_days) for s in range(num_shifts) for p in range(num_people)))

# 求解
solver = cp_model.CpSolver()
solver.Solve(model)

# 输出结果
for d in range(num_days):
    print(f"Day {d + 1}:")
    for s in range(num_shifts):
        assigned = [all_people[p] for p in range(num_people) if solver.Value(schedule[d, s, p]) == 1]
        print(f"  Shift {s + 1}: {', '.join(assigned)}")
