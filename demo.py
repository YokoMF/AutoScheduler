# 定义三个组的成员
A_group = ["陈雪莲", "邱凌", "卓燕斌", "万米",
           "包云飞", "沈毅", "蒋炯明", "王仲晖",
           "徐蒲金", "秦刚", "胡继云", "刘敏",
           "郭天赐", "孙俊敏", "陈栋"]
B_group = ["张南", "徐升", "余行方"]
C_group = ["祁玉权", "何超超"]
employees = A_group + B_group + C_group
last_inprduct_person = "胡继云"
# 构建索引映射
person_index = {p: i for i, p in enumerate(employees)}


index = person_index[last_inprduct_person]
next_index = (index + 1) % len(A_group)
next_person = A_group[next_index]
print(next_person)

print(B_group.index("余行方"))