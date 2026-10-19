import argparse, hashlib, json, os, sqlite3, sys, time
from pathlib import Path
sys.path.insert(0,'/workspace/scratch/0229a0b41cd2/OntoKin')
from ontokin.agent_store import AgentStore, dumps
p=argparse.ArgumentParser();p.add_argument('--mode',default='WAL');p.add_argument('--count',type=int,default=1500);a=p.parse_args()
root=Path('/workspace/scratch/0229a0b41cd2')/('sqlite-store-diagnostic-'+a.mode.lower()+'-'+str(time.time_ns()))
root.mkdir(); store=AgentStore(root,{'implementation':'diagnostic'})
if a.mode!='WAL':
 with store.connection() as db: db.execute('PRAGMA journal_mode='+a.mode)
log=(root/'diagnostic.jsonl').open('w')
def note(obj):
 line=json.dumps(obj,sort_keys=True);log.write(line+'\n');log.flush()
 if obj['event']!='progress' or obj['iteration']%100==0:print(line,flush=True)
def files():
 out={}
 for path in root.iterdir():
  if path.name.startswith('agent.sqlite3'):
   st=path.stat();out[path.name]={'size':st.st_size,'inode':st.st_ino,'mtime_ns':st.st_mtime_ns}
 return out
def verify(i, stage, expected_state):
 with store.connection() as db:
  row=store.request(db,'p'+str((i-1)//20),'r'+str(i))
  extent=db.execute('SELECT count(*), max(sequence) FROM requests').fetchone()
  if row is None or row['state']!=expected_state or tuple(extent)!=(i,i):
   note({'event':'invariant-failed','iteration':i,'stage':stage,'row':None if row is None else {'id':row['id'],'state':row['state'],'sequence':row['sequence']},'count_max':list(extent),'files':files()})
   raise RuntimeError('store lost committed identities')
started=time.monotonic()
try:
 with store.connection() as db:
  note({'event':'started','mode':db.execute('PRAGMA journal_mode').fetchone()[0],'sqlite':sqlite3.sqlite_version,'sqlite_source_id':db.execute('SELECT sqlite_source_id()').fetchone()[0],'path':str(root),'python':sys.version,'count':a.count})
 for i in range(1,a.count+1):
  request={'project_id':'p'+str((i-1)//20),'request_id':'r'+str(i),'operation':'inspect','padding':('data-'+str(i))*1500}
  payload=dumps(request);response={**{k:request[k] for k in ('project_id','request_id','operation')},'status':'queued'}
  with store.transaction() as db:
   store.recover(db)
   store.record(db,request,hashlib.sha256(payload.encode()).hexdigest(),payload,response)
  verify(i,'queued','queued')
  with store.transaction() as db:
   store.recover(db)
   row=db.execute("SELECT * FROM requests WHERE state='queued' ORDER BY sequence LIMIT 1").fetchone()
   response['status']='running';store.update_response(db,request['project_id'],request['request_id'],response)
   db.execute('UPDATE requests SET owner=? WHERE sequence=?',(store.owner,row['sequence']))
  verify(i,'running','running')
  for n in range(3): verify(i,'working-'+str(n),'running')
  response['status']='succeeded';response['result']='result-'+str(i)+'x'*6000
  with store.transaction() as db:
   row=store.request(db,request['project_id'],request['request_id'])
   if row is None: raise RuntimeError('missing at commit')
   store.update_response(db,request['project_id'],request['request_id'],response)
   db.execute('UPDATE requests SET owner=NULL WHERE sequence=?',(row['sequence'],))
  verify(i,'terminal','succeeded')
  if i%20==0:note({'event':'progress','iteration':i,'elapsed':round(time.monotonic()-started,3),'files':files()})
 note({'event':'passed','iterations':a.count,'elapsed':round(time.monotonic()-started,3),'files':files()})
except Exception as e:
 note({'event':'failed','exception':type(e).__name__,'reason':str(e),'elapsed':round(time.monotonic()-started,3),'files':files()})
 raise
finally:
 log.close()
 store.close()
