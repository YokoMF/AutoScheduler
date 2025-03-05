from ortools.sat.python import cp_model

# 设定天数（假设 30 天）
num_days = 30
num_teams = 3  # A, B, C
A, B, C = 0, 1, 2  # 三个班组的索引

# 法定节假日（示例，假设 5 号、12 号、18 号是法定假日）
holidays = {5, 12, 18}

# 创建 OR-Tools 模型
model = cp_model.CpModel()

# 定义变量：schedule[day][team] -> 0 或 1（0 = 休息, 1 = 工作）
schedule = [[model.NewBoolVar(f"day_{d}_team_{t}") for t in range(num_teams)] for d in range(num_days)]

# 设定 A 组正常排班（周二到周六工作，周日周一休息）
for d in range(num_days):
    if d % 7 in [0, 1]:  # 周日（0）、周一（1）休息
        model.Add(schedule[d][A] == 0)
    else:
        model.Add(schedule[d][A] == 1)

# 设定 B 组正常排班（周日到周四工作，周五周六休息）
for d in range(num_days):
    if d % 7 in [5, 6]:  # 周五（5）、周六（6）休息
        model.Add(schedule[d][B] == 0)
    else:
        model.Add(schedule[d][B] == 1)

# 设定 C 组正常排班（周一到周五工作，周六周日休息）
for d in range(num_days):
    if d % 7 in [6, 0]:  # 周六（6）、周日（0）休息
        model.Add(schedule[d][C] == 0)
    else:
        model.Add(schedule[d][C] == 1)


# 处理法定节假日影响
for holiday in holidays:
    if holiday + 1 < num_days:
        # A 组：法定假日后最近的周二休假
        after_holiday = next((d for d in range(holiday + 1, num_days) if d % 7 == 2), None)
        if after_holiday:
            model.Add(schedule[after_holiday][A] == 0)

        # B 组：法定假日后最近的周四休假
        after_holiday = next((d for d in range(holiday + 1, num_days) if d % 7 == 4), None)
        if after_holiday:
            model.Add(schedule[after_holiday][B] == 0)

# 求解
solver = cp_model.CpSolver()
solver.Solve(model)

# 打印排班结果
for d in range(num_days):
    print(f"Day {d + 1:2d} | A: {solver.Value(schedule[d][A])} | B: {solver.Value(schedule[d][B])} | C: {solver.Value(schedule[d][C])}")
