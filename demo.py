from datetime import date
from components.rules.uatshift import ApplicationRuleNormal

when_start = date(2025,4,1)
when_end = date(2025,4,30)

apc = ApplicationRuleNormal(when_start, when_end)
apc.schedule()
apc.pretty_format()
apc.dump_to_excel()

from components.report import RenderExcel

excel = RenderExcel(r"output.xlsx")
excel.render()