"""Summarize a completed arm from the operator's serial dispatch ledger."""
import argparse
from collections import Counter
import json
from pathlib import Path

def summarize(folder):
    events=[json.loads(line) for line in (folder/'calls.jsonl').read_text().splitlines()]
    end=json.loads((folder/'finish.json').read_text())
    counts=Counter();usage=Counter();seconds=Counter();failed_commands=[];active={};commands=[]
    for e in events:
        event=e['event'];kind=e.get('kind')
        if event=='dispatch':
            counts[kind]+=1;active[kind]=e['elapsed']
            if kind=='tool':
                commands.append(e['argv'][-1])
        if event in {'returned','deadlineDuringOperation','launchError'} and kind in active:
            seconds[kind]+=e['elapsed']-active.pop(kind)
        if event=='usage':
            for k,v in e['normalized'].items():usage[k]+=v
        if event=='guestResult' and e['receipt']['exit']!=0:
            failed_commands.append({'turn':e['turn'],'exit':e['receipt']['exit'],'stderr':e['receipt'].get('stderr','')})
    if usage['charged']!=end['knownCharged']:raise ValueError('ledger differs from final accounting')
    return {'status':end['status'],'setupSeconds':end['setupSeconds'],'wallSeconds':end['elapsedSeconds'],
            'usageWithReceipts':dict(usage),'calls':dict(counts),'secondsInCalls':dict(seconds),
            'declinedOperations':[{'kind':e['kind'],'reason':e['reason']} for e in events if e['event']=='refused'],
            'failedGuestCommands':failed_commands,'formatRejections':sum(e['event']=='formatRejected' for e in events),
            'literalRepeatCommands':sum(v-1 for v in Counter(commands).values()),'operatorInterventionsDuringArm':0,
            'incompleteModelUsage':any(e.get('incompleteModelUsage') for e in events)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('arm',type=Path)
    args=p.parse_args();print(json.dumps(summarize(args.arm),indent=2))
