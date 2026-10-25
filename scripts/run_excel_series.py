"""Run all three benchmark trials; record every outcome without silent replacement."""
import argparse
from hashlib import sha256
from contextlib import closing
import json
from pathlib import Path
import shutil
from uuid import uuid4
from accounting_finance_agent.config import EXCEL_PROFILE, PROJECT_ROOT, load_settings
from accounting_finance_agent.__main__ import run_prompt
from accounting_finance_agent.provenance import effective_configuration
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.worklog import WorkLog
from accounting_finance_agent.workspace import thread_workspace
from grade_excel_benchmark import grade


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run: parser.error('Use --run to start three paid model/sandbox trials.')
    settings=load_settings(require_sandbox=True,profile=EXCEL_PROFILE)
    assets=PROJECT_ROOT/'evaluations/excel-v1'
    fixture_hashes={p.relative_to(assets).as_posix():sha256(p.read_bytes()).hexdigest()
                    for p in assets.rglob('*') if p.is_file()}
    configuration=effective_configuration(settings)
    record={'configuration':configuration,'fixture_sha256':fixture_hashes,'runs':[],'human_review':'pending'}
    output=PROJECT_ROOT/'.state/evaluations'/('excel-'+str(uuid4())+'.json');output.parent.mkdir(parents=True,exist_ok=True)
    with open_history(mode='excel-evaluation') as history, closing(WorkLog()) as log:
        for n in range(3):
            thread=history.new();folder=thread_workspace(thread.id)
            for source in (PROJECT_ROOT/'evaluations/excel-v1/agent-inputs').iterdir():
                shutil.copyfile(source,folder/source.name)
            item={'ordinal':n+1,'thread':thread.id}
            try:
                run_prompt(settings,history,log,thread.id,(folder/'task.txt').read_text(),sandbox=True)
                current={p.relative_to(assets).as_posix():sha256(p.read_bytes()).hexdigest()
                         for p in assets.rglob('*') if p.is_file()}
                if current!=fixture_hashes or effective_configuration(settings)['configuration_sha256']!=configuration['configuration_sha256']:
                    raise RuntimeError('Configuration/fixture changed during the series; start a new series.')
                item['grader']=grade(folder)
            except Exception as exc:
                item['error']=type(exc).__name__
            record['runs'].append(item)
            output.write_text(json.dumps(record,indent=2))
    print(output)

if __name__=='__main__': main()
