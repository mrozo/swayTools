#!/usr/bin/env python3
import subprocess
import json
import datetime
import time

def subscribe(eventTypes, changes=None):
    eventTypesArg="[\"" + "\",\"".join(eventTypes) + "\"]"
    for event in subprocess.Popen(['/usr/bin/swaymsg', '-m', '-t', 'subscribe' , eventTypesArg], stdout=subprocess.PIPE).stdout:
        e = json.loads(event)
        if changes is None or e['change'] in changes:
            yield e

def getTree():
    ps = subprocess.Popen(['swaymsg','-t','get_tree','-r'], stdin = subprocess.PIPE,stdout = subprocess.PIPE)
    (stdout, stderr) = ps.communicate()
    return json.loads(stdout)

def findWindows(tree, workspaceId=None):
    if tree['type'] == 'workspace':
        workspaceId = tree['id']
    for n in tree['nodes']:
        if n['type'] == 'con' and 'pid' in n:
            yield (workspaceId, n)
        else:
            if 'nodes' in n:
                yield from findWindows(n,workspaceId=workspaceId)

def getWindowsOnActiveWorkspace(windows=None):
    tree=windows or findWindows(getTree())
    activeWorkspace=None
    workspaces={}
    activeWorkspace=[]
    for winWorkspace, window in tree or getTree():
        workspaces.setdefault(winWorkspace, list()).append(window)
        if window['focused']:
            activeWorkspace=workspaces[winWorkspace]
    return activeWorkspace
    
def setBorder(window, border):
    subprocess.run(['swaymsg', f"[con_id={window['id']}] border {border}"])

    
if __name__ == "__main__":
    originalBorders={}
    for e in subscribe(['window'], ['focus','close','title']):
        print(f"{datetime.datetime.now()} : {e['change']}")
        
        if e['change'] == 'close' and e['container']['id'] in originalBorders.keys():
            del originalBorders[e['container']['id']]
            continue

        if e['change'] == 'title':
            if e['container']['id'] not in originalBorders.keys():
                time.sleep(0.05) # yep, thats dumb but it works
                window = list(filter(lambda w: w['focused'], getWindowsOnActiveWorkspace()))
                if len(window):
                    window=window[0]
                    print(f"window {window['id']} - border={window['border']}")
                    originalBorders[window['id']] = window['border']
            continue
        focused=e['container']
        windows=getWindowsOnActiveWorkspace()
        if len(windows) == 1:
            setBorder(windows[0], 'none')
            if windows[0]['id'] not in originalBorders.keys():
                originalBorders[windows[0]['id']] = windows[0]['border']
        else:
            for window in windows:
                if window['id'] in originalBorders.keys():
                    print(f"window '{window['id']} set border '{originalBorders[window['id']]}'")
                    setBorder(windows[0], originalBorders[window['id']])
                
        
        
