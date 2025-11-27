from openpyxl import Workbook
import os
os.makedirs('docs', exist_ok=True)
wb = Workbook()
ws = wb.active
ws.title = 'PlanTemplate'
# headers
ws.append(['code','name','credits','hours_theory','hours_practice','cycle'])
# example rows
ws.append(['131B10012','CALCULO DIFERENCIAL',4,3,2,2])
ws.append(['131B10007','INGLES BASICO II',2,1,2,2])
# save
wb.save('docs/plan_import_template.xlsx')
print('Created docs/plan_import_template.xlsx')
