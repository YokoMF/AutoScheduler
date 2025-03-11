# 约束2 安排双休日值班
for d in weekend_days:
    model.AddExactlyOne(vacation[(person_index[e], d)] for e in group_a)
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

avg = (total_a + len(working_days)) // len(group_a)
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

