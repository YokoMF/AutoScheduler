# 约束2 安排双休日值班
weekend_days = [(day - self.start).days for day in self.shiftcalendar.get_days("uat-weekend")]
for d in weekend_days:
    if (self.start + timedelta(days=d)).weekday() == 5:
        model.Add(sum(vacation[(person_index[e], 1, d)]
                      for e in group_a) == 1)
        model.Add(sum(vacation[(person_index[e], 1, d)]
                      for e in group_b) == 1)
    if (self.start + timedelta(days=d)).weekday() == 6:
        model.Add(sum(vacation[(person_index[e], 1, d)]
                      for e in group_a) == 1)
        model.Add(sum(vacation[(person_index[e], 1, d)]
                      for e in group_c) == 1)

# 约束3 安排工作日值班
working_days = [(day - self.start).days for day in self.shiftcalendar.get_days("uat-night")]
for d in working_days:
    model.Add(sum(vacation[(person_index[e], 2, d)]
                  for e in group_a) == 1)

# 约束4 双休日及投产值班人员公平分配
avg = total_a // len(group_a)
spdays = inproduct_days + weekend_days
for d in spdays:
    for e in group_a:
        total = sum(vacation[(person_index[e], s, d)] for s in range(2))
        model.Add(total >= avg)
        model.Add(total <= avg + 1)

mfdays = [(d - self.start).days for d in self.shiftcalendar.holidays if d.weekday() == 5]
avg = len(mfdays) // len(group_b)
for d in mfdays:
    for e in group_b:
        total = sum(vacation[(person_index[e], s, d)] for s in range(2))
        model.Add(total >= avg)
        model.Add(total <= avg + 1)

mfdays = [(d - self.start).days for d in self.shiftcalendar.holidays if d.weekday() != 5]
avg = len(mfdays) // len(group_c)
for d in mfdays:
    total = sum(vacation[(person_index[e], 2, d)] for e in group_c)
    model.Add(total >= avg)
    model.Add(total <= avg + 1)


