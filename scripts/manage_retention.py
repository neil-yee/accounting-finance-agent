"""Explicit closure/pruning; defaults to a plan. Final files stay in owner archives."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.lifecycle import mark_closed, retention_candidates, archive_run
from accounting_finance_agent.worklog import WorkLog, thread_lease
from langgraph.checkpoint.sqlite import SqliteSaver


def request_hosted_deletion(run_ids):
    from langsmith import Client
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    client=Client()
    groups={}
    for run_id in run_ids:
        try:
            run=client.read_run(run_id)
        except Exception as exc:
            # Do not treat connectivity/permission failures as successful deletion.
            from langsmith.utils import LangSmithNotFoundError
            if isinstance(exc, LangSmithNotFoundError): continue
            raise
        if run.parent_run_id is not None or str(run.id)!=run_id:
            raise ValueError('Retention requires the recorded root run identity.')
        groups.setdefault(str(run.session_id),[]).append(str(run.trace_id))
    for session,ids in groups.items():
        for start in range(0,len(ids),1000):
            client._request_with_retries('POST','/runs/delete',json={'session_id':session,'trace_ids':ids[start:start+1000]})
    return not groups  # Queued deletes are asynchronous; retry verification later.


def prune(thread_id, *, hosted=False):
    from uuid import UUID
    thread_id=str(UUID(thread_id))
    with thread_lease(thread_id):
        folder=PROJECT_ROOT/'workspace/threads'/thread_id
        archive=None
        if folder.exists():
            from uuid import uuid4
            archive=archive_run('retained-'+str(uuid4()),folder)
            shutil.rmtree(folder)
        roots=[PROJECT_ROOT/'.state/checkpoints.sqlite']
        roots+=list((PROJECT_ROOT.parent/'accounting-finance-agent-archives').glob('*/checkpoints.sqlite'))
        for database in roots:
            if database.is_file():
                with sqlite3.connect(database) as conn:
                    saver=SqliteSaver(conn);saver.delete_thread(thread_id)
                    tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    for table in ('finance_threads','finance_active_threads'):
                        if table in tables: conn.execute('DELETE FROM '+table+' WHERE thread_id=?',(thread_id,))
                    conn.commit()
                    conn.execute('VACUUM')
        # Restrict local trace removal to roots belonging to this thread.
        with closing(WorkLog()) as log:
            ids=[r[0] for r in log.conn.execute('SELECT id FROM runs WHERE thread_id=?',(thread_id,))]
        for run_id in ids:
            (PROJECT_ROOT/'traces'/('trace-'+run_id+'.json')).unlink(missing_ok=True)
        # Retain final artifacts/inputs/supporting code; remove old staging scratch.
        archives=PROJECT_ROOT.parent/'accounting-finance-agent-archives'
        for metadata in archives.glob('*/archive.json'):
            if json.loads(metadata.read_text()).get('thread') != thread_id: continue
            files=metadata.parent/'files'
            finals={p.parent for p in files.rglob('working-paper.xlsx') if 'staging' not in p.parts}
            for candidate in sorted(files.rglob('*'),reverse=True):
                if not candidate.is_file(): continue
                keep=(candidate.suffix=='.py' or candidate.name in {'source.csv','notes.json','task.txt'}
                      or any(candidate.is_relative_to(root) for root in finals))
                if not keep: candidate.unlink()
        # Retain the closure marker until hosted deletion is confirmed.
        if hosted and request_hosted_deletion(ids):
            (PROJECT_ROOT/'.state/closed-threads'/(thread_id+'.json')).unlink(missing_ok=True)
        return str(archive) if archive else None


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--close',metavar='THREAD_ID');p.add_argument('--apply',action='store_true');p.add_argument('--hosted',action='store_true',help="Also queue/verify deletion of this app recorded root traces.")
    a=p.parse_args()
    if a.close: mark_closed(a.close)
    candidates=retention_candidates()
    result={'eligible_closed_threads':candidates,'applied':a.apply,'hosted_traces':'Use --apply --hosted to queue and later verify exact recorded trace deletions.'}
    if a.apply: result['retained_archives']={thread:prune(thread,hosted=a.hosted) for thread in candidates}
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
