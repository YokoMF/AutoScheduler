from components.rules.operation import (OperationRuleDay,
                                        OperationRuleBase,
                                        OperationRuleNight,
                                        OperationRuleMiddle,
                                        PARAMETERS)


for rule_name in PARAMETERS["operation"]:
    for i in range(len(PARAMETERS["operation"][rule_name])):
        rule = eval(f"{rule_name}")(i, 2025, 3)
        rule.schedule()
        rule.commit()

from components.report import DutyReport
report = DutyReport(2025, 3)
report.display()