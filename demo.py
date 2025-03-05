from ortools.sat.python import cp_model
import calendar
import datetime

# 定义模型
model = cp_model.CpModel()


# 定义环境变量
year = 2025
month = 5
max_vacation_days = 11
num_employees = 3
_, num_days = calendar.monthrange(year, month)
all_days = [datetime.date(year, month, d).weekday() for d in range(1, num_days + 1)]

# 模型变量： 每个值班人员每一天的工作状态{0: 工作, 1: 休假}
vacation = dict()
no_duty = list()
for e in range(num_employees):
    for d in range(num_days):
        vacation[(e, d)] = model.NewBoolVar(f"{e}_day_{d}")

# 每个人每个月最多休假 max_vacation_days 天
for e in range(num_employees):
    model.Add(sum(vacation[(e, d)] for d in range(num_days)) == max_vacation_days)

# 周日与周一休假
balance = datetime.date(year, month, 1).weekday()
for e in range(num_employees):
    for d in range(num_days):
        if (d + balance) % 7 in [6, 0]:
            model.Add(vacation[(e, d)] == 1)

# 优先选择周四补休
rest_days =max_vacation_days - all_days.count(0) - all_days.count(6)
if rest_days <= all_days.count(3):
    for e in range(num_employees):
        model.Add(sum(vacation[(e, d)] for d in range(num_days) if (d + balance) % 7 == 3) == rest_days)
else:
    for e in range(num_employees):
        model.Add(sum(vacation[(e, d)] for d in range(num_days) if (d + balance) % 7 == 3) == all_days.count(3))

# 目标函数：尽量避免两人同时在周四休息
all_sp_days = [d - 1 for d in range(1, num_days + 1) if datetime.date(year, month, d).weekday() == 3]
violation = {}

for d in all_sp_days:
    violation[d] = model.NewBoolVar(f"violation_{d}")
    model.Add(sum(vacation[(e, d)] for e in range(num_employees)) < num_employees).OnlyEnforceIf(violation[d].Not())
    model.Add(sum(vacation[(e, d)] for e in range(num_employees)) == num_employees).OnlyEnforceIf(violation[d])

# 定义目标函数
model.Minimize(sum(violation[d] for d in all_sp_days))

# 求解
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for e in range(num_employees):
        print(f"Employee {e}: ", end="")
        for d in range(num_days):
            print(f"{solver.Value(vacation[(e, d)])} ", end="")
        print()