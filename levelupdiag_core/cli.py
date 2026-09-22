from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .config import ConfigError,load_config
from .manifest import ManifestError,load_manifest,get_campaign
from .runner import run_campaign,run_named_sequence,_print_actionable_findings
from .verdicts import exit_code,aggregate_verdicts
from .worker import run_worker

def main(argv=None):
    p=argparse.ArgumentParser(prog='levelupdiag',description='Konnaxion LevelUpDiag upgraded engine')
    p.add_argument('--target',help='Override target repository root')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('doctor'); sub.add_parser('list'); sub.add_parser('triage-current')
    r=sub.add_parser('run'); r.add_argument('campaign',nargs='?',default='connection-debug')
    rs=sub.add_parser('run-sequence'); rs.add_argument('sequence',nargs='?',default='recommended-debug')
    w=sub.add_parser('_worker'); w.add_argument('--level',required=True); w.add_argument('--output',required=True); w.add_argument('--target',dest='worker_target')
    args=p.parse_args(argv); root=Path(__file__).resolve().parents[1]
    try:
        if args.cmd=='_worker':
            result=run_worker(root,args.level,Path(args.output),args.worker_target); return exit_code(result.verdict)
        cfg=load_config(root,args.target)
        if args.cmd=='doctor':
            m=load_manifest(root); print('LevelUpDiag Konnaxion doctor: PASS'); print(f'tool_root: {root}'); print(f'target_root: {cfg.target_root_path}'); print(f'control_root: {cfg.control_root_path}'); print(f'levels: {len(m["levels"])}'); return 0
        if args.cmd=='list':
            m=load_manifest(root)
            print('Campaigns:')
            for n,c in m['campaigns'].items(): print(f"  {n}: {' -> '.join(c['levels'])}")
            print('Sequences:')
            for n,s in m.get('sequences',{}).items(): print(f"  {n}: {' -> '.join(s['campaigns'])}")
            return 0
        if args.cmd=='triage-current':
            from .reports import read_level_result
            levels_root=cfg.control_root_path/'current'/'levels'
            if not levels_root.is_dir():
                print('No current LevelUpDiag run found.'); return 20
            found=False
            for result_path in sorted(levels_root.glob('n*/result.json')):
                result=read_level_result(result_path)
                if result.verdict in {'PASS','SKIP'}:
                    continue
                found=True
                print(f'{result.level} {result.verdict} {result.name}')
                _print_actionable_findings(result, evidence_chars=1800)
            summary_path=cfg.control_root_path/'current'/'summary.json'
            if summary_path.is_file():
                try:
                    summary=json.loads(summary_path.read_text(encoding='utf-8'))
                    protection=summary.get('target_protection')
                    if isinstance(protection,dict) and protection.get('verdict'):
                        found=True
                        print(f"TARGET_PROTECTION {protection.get('verdict')}")
                        print(f"    {protection.get('message','Tracked target state changed during diagnostics.')}")
                        before=str(protection.get('before','')).strip()
                        after=str(protection.get('after','')).strip()
                        if before:
                            print('    before:')
                            for line in before.splitlines()[-12:]: print(f'      {line}')
                        if after:
                            print('    after:')
                            for line in after.splitlines()[-12:]: print(f'      {line}')
                except (OSError,ValueError,TypeError,json.JSONDecodeError):
                    pass
            if not found:
                print('Current run has no non-PASS levels or target-protection errors.')
            return 0
        if args.cmd=='run':
            result=run_campaign(args.campaign,config=cfg); print(f'campaign {result.campaign}: {result.verdict}'); return exit_code(result.verdict)
        if args.cmd=='run-sequence':
            outcomes=run_named_sequence(args.sequence,cfg); verdict=aggregate_verdicts([x.verdict for x in outcomes]); print(f'sequence {args.sequence}: {verdict}'); return exit_code(verdict)
    except (ConfigError,ManifestError,ValueError,OSError) as exc:
        print(f'LevelUpDiag error: {exc}',file=sys.stderr); return 30
    return 64
