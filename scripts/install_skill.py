#!/usr/bin/env python3
"""Copy this skill to a documented host directory; never overwrite an install."""
import _bootstrap
import argparse,pathlib,shutil,sys

def install(agent,scope,project=None,destination=None):
    base=pathlib.Path(project or pathlib.Path.cwd()) if scope=='project' else pathlib.Path.home()
    parent=base/('.agents' if agent=='codex' else '.claude')/'skills'
    target=pathlib.Path(destination).expanduser() if destination else parent/'jev-for-agent'
    source=_bootstrap.ROOT.resolve();target=target.resolve()
    if target==source or source in target.parents:
        raise ValueError('Destination cannot be inside the source skill')
    if target.exists():raise FileExistsError('Destination already exists; inspect and back it up before replacing')
    def ignore(directory,names):
        return [n for n in names if n in {'.git','__pycache__','.venv','node_modules','work','.DS_Store'} or n.endswith('.pyc') or (n.startswith('.env') and n!='.env.example')]
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,target,ignore=ignore)
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--agent',required=True,choices=['codex','claude']);p.add_argument('--scope',choices=['user','project'],default='project')
    p.add_argument('--project');p.add_argument('--destination',help='Explicit skill folder for another compatible host or a staging install')
    a=p.parse_args()
    try:print('Installed:',install(a.agent,a.scope,a.project,a.destination));return 0
    except (OSError,ValueError) as e:print(type(e).__name__+': installation stopped; destination may need inspection');return 1
if __name__=='__main__':sys.exit(main())
