"""Materialize fixed agent-only inputs and separate independent evaluator assets."""
import csv
from decimal import Decimal
import json
from pathlib import Path
from accounting_finance_agent.config import PROJECT_ROOT


def prepare(destination):
    doc = (PROJECT_ROOT/'docs/evaluations/excel-benchmark.md').read_text()
    rows=[]
    for line in doc.splitlines():
        parts=[v.strip() for v in line.strip('|').split('|')]
        if len(parts)==5 and parts[0] in {'Revenue','Cost of sales','Operating expense','Finance expense','Tax expense'}:
            rows.append([parts[0],parts[1],parts[2].replace(',',''),parts[3].replace(',',''),parts[4]])
    assert len(rows)==13
    root=Path(destination); inputs=root/'agent-inputs'; evaluator=root/'evaluator'
    inputs.mkdir(parents=True,exist_ok=True); evaluator.mkdir(parents=True,exist_ok=True)
    with (inputs/'source.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['Classification','Category','January','February','Note ID']);w.writerows(rows)
    notes=doc.split('**Business notes supplied to the agent**')[1].split('## 2.')[0].strip()
    (inputs/'notes.json').write_text(json.dumps({'company':'Harbor Office Supplies & Services','currency':'USD','periods':['January 2026','February 2026'],'notes':notes},indent=2))
    contract=doc.split('## 2. Calculation contract')[1].split('## 3.')[0].strip()
    prompt='''Create a professionally formatted synthetic Excel working paper for the supplied two months. Use only source.csv and notes.json for facts. Deliver one final working-paper.xlsx with exactly these sheets in order: Inputs, Income Statements, Analysis, Checks. Include each supplied category, all income-statement totals, both margins, monthly variances and profit bridge, detailed grounded analysis and reconciliation checks. Preserve source files. Label period, USD and synthetic data. Use the exact source category labels and the subtotal labels Revenue, Cost of sales, Gross profit, Operating expenses, Operating profit, Pretax profit, Net income, Gross margin, Net margin. On statement rows place January and February numeric amounts in the first two cells following each label. On Analysis, use the exact category labels plus Gross margin and Net margin as row labels; put January, February, amount change and percentage change in the four immediately following cells. For margin rows the third value is the fractional margin difference and must be displayed/labeled as percentage points. Zero-base percentages must be N/A. Include a Profit change bridge row with the calculated net-income change immediately following the label. Analysis must cover every category and supplied note, variances, zero-base handling, margins and the profit bridge. Build formulas linked to inputs, recalculate with LibreOffice and preserve cached values; use the approved recalculation helper for rendered page evidence. Return supporting code and actual-check reports; visual/meaning review remains human work.\n'''+contract
    (inputs/'task.txt').write_text(prompt)
    expected={}
    for col,month in [(2,'January'),(3,'February')]:
        totals={kind:sum((Decimal(r[col]) for r in rows if r[0]==kind),Decimal(0)) for kind in ['Revenue','Cost of sales','Operating expense','Finance expense','Tax expense']}
        gp=totals['Revenue']-totals['Cost of sales'];op=gp-totals['Operating expense'];pre=op-totals['Finance expense'];net=pre-totals['Tax expense']
        expected[month]={**{r[1]:str(Decimal(r[col])) for r in rows},'Revenue':str(totals['Revenue']),'Cost of sales':str(totals['Cost of sales']),'Gross profit':str(gp),'Operating expenses':str(totals['Operating expense']),'Operating profit':str(op),'Pretax profit':str(pre),'Net income':str(net),'Gross margin':str(gp/totals['Revenue']),'Net margin':str(net/totals['Revenue'])}
    (evaluator/'oracle.json').write_text(json.dumps(expected,indent=2))
    (evaluator/'rubric.md').write_text(doc.split('## 4. Acceptance rubric')[1])
    (evaluator/'series.json').write_text(json.dumps({'runs':3,'fresh_threads':True,'all_must_pass':True,'human_review_required':True},indent=2))
    return root

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    print(prepare(p.parse_args().destination))
