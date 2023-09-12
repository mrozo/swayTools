#!/usr/bin/env python3
import json
import subprocess
import time


def match_event(event, changes=None):
    if changes is None or event['change'] in changes:
        return True
    return False


def subscribe(event_types, changes=None):
    event_types_arg = "[\"" + "\",\"".join(event_types) + "\"]"
    events_raw_stream = subprocess.Popen(['/usr/bin/swaymsg', '-m', '-t', 'subscribe', event_types_arg],
                                         stdout=subprocess.PIPE).stdout
    return filter(lambda e: match_event(e, changes), map(json.loads, events_raw_stream))


def get_tree():
    ps = subprocess.Popen(['swaymsg', '-t', 'get_tree', '-r'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, stderr) = ps.communicate()
    return json.loads(stdout)


def find_windows(tree, workspace_id=None):
    if tree['type'] == 'workspace':
        workspace_id = tree['id']
    for n in tree['nodes']:
        if n['type'] == 'con' and 'pid' in n:
            yield workspace_id, n
        else:
            if 'nodes' in n:
                yield from find_windows(n, workspace_id=workspace_id)


def get_windows_on_active_workspace(windows=None):
    tree = windows or find_windows(get_tree())
    workspaces = {}
    active_workspace = []
    for winWorkspace, window in tree or get_tree():
        workspaces.setdefault(winWorkspace, list()).append(window)
        if window['focused']:
            active_workspace = workspaces[winWorkspace]
    return active_workspace


def set_border(window, border):
    subprocess.run(['swaymsg', f"[con_id={window['id']}] border {border}"])


def set_borders_on_workspace(windows, original_borders):
    if len(windows) == 1:
        set_border(windows[0], 'none')
        if windows[0]['id'] not in original_borders.keys():
            original_borders[windows[0]['id']] = windows[0]['border']
    else:
        for window in windows:
            if window['id'] in original_borders.keys():
                print(f"window '{window['id']} set border '{original_borders[window['id']]}'")
                set_border(windows[0], original_borders[window['id']])


def save_original_border(original_borders):
    window = list(filter(lambda w: w['focused'], get_windows_on_active_workspace()))
    if len(window):
        window = window[0]
        print(f"window {window['id']} - border={window['border']}")
        original_borders[window['id']] = window['border']


def dispatch_event(e, original_borders):
    if e['change'] == 'close' and e['container']['id'] in original_borders.keys():
        del original_borders[e['container']['id']]
    elif e['change'] == 'title':
        if e['container']['id'] not in original_borders.keys():
            time.sleep(0.05)  # yep, that`s dumb but it works
            save_original_border(original_borders)
    else:
        set_borders_on_workspace(get_windows_on_active_workspace(), original_borders)


if __name__ == "__main__":
    original_borders = {}
    for event in subscribe(['window'], ['focus', 'close', 'title']):
        dispatch_event(event, original_borders)
