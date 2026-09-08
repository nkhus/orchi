#!/usr/bin/env python3
"""Use a foreground task's bounded read/scope channel, never a control store."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import socket
import sys
import uuid


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    r = sub.add_parser('read'); r.add_argument('path')
    r.add_argument('--view', choices=['code','current','target','epic-design'], default='code')
    r.add_argument('--content-hash'); r.add_argument('--start-line', type=int, default=1)
    r.add_argument('--end-line', type=int); r.add_argument('--consistency', choices=['fixed','snapshot'], default='fixed')
    s = sub.add_parser('scope'); s.add_argument('--file', required=True)
    a = p.parse_args(argv)
    try:
        if a.command == 'read':
            arguments = {k:v for k,v in vars(a).items() if k != 'command' and v is not None}
        else:
            if a.file == '-':
                raw = sys.stdin.read(60_001)
                if len(raw.encode()) > 60_000:
                    raise ValueError('Scope request exceeds the channel limit')
            else:
                source = Path(a.file)
                if source.is_symlink() or source.stat().st_size > 60_000:
                    raise ValueError('Use a bounded regular JSON scope-request file')
                raw = source.read_text()
            arguments = json.loads(raw)
        request = {'token':os.environ['ORCHI_CHANNEL_TOKEN'],'id':uuid.uuid4().hex,
                   'operation':a.command,'arguments':arguments}
        message = json.dumps(request).encode() + b'\n'
        if len(message) > 65_536:
            raise ValueError('Request exceeds the channel limit')
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(45)
            client.connect(os.environ['ORCHI_CHANNEL_SOCKET'])
            client.sendall(message)
            with client.makefile('rb') as response:
                line = response.readline(1_000_001)
                if len(line) > 1_000_000 or not line.endswith(b'\n'):
                    raise ValueError('Invalid or excessive channel response')
                result = json.loads(line)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('ok') else 2
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(json.dumps({'ok':False,'code':'CHANNEL_UNAVAILABLE','message':str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
