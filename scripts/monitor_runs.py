"""Owner monitoring summary, using existing run and API-ledger records."""
from contextlib import closing
import json
from accounting_finance_agent.worklog import WorkLog


def summary(log):
    rows=log.conn.execute('SELECT id,thread_id,status,started,finished,error_type FROM runs ORDER BY started DESC LIMIT 100').fetchall()
    result=[]
    for row in rows:
        item=dict(row); signals=[]
        if item['status'] in ('failed','limited','running'): signals.append('investigate before using outputs')
        events=log.conn.execute("SELECT kind,details FROM events WHERE run_id=? ORDER BY id",(item['id'],)).fetchall()
        item['api_attempts']=sum(e['kind']=='api_reserved' for e in events)
        ledger=[json.loads(e['details']) for e in events if e['kind'] in ('api_reserved','api_usage')]
        item['committed_usd']=ledger[-1].get('committed_usd') if ledger else None
        if item['committed_usd'] is not None and float(item['committed_usd'])>=1: signals.append('API budget exhausted')
        item['signals']=signals;item['review_required']=item['status']=='needs_review'
        result.append(item)
    return result

if __name__=='__main__':
    with closing(WorkLog()) as log: print(json.dumps(summary(log),indent=2))
