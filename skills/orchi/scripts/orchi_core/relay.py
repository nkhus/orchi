"""Foreground, ticket-bound local RPC. No arbitrary CLI, approval or store access.

The outer sandbox must permit this local socket and keep other workers away from
its capability. A shared OS identity is not a security boundary.
"""
from __future__ import annotations

import hmac
import json
from pathlib import Path
import secrets
import shutil
import socketserver
import tempfile
import threading

from pydantic import ValidationError
from .common import OrchiError, require


class WorkerRelay:
    def __init__(self, engine, ticket_id: str, phase: str):
        self.engine, self.ticket_id, self.phase = engine, ticket_id, phase
        self.token = secrets.token_hex(32)
        self.directory = Path(tempfile.mkdtemp(prefix='orchi-channel-'))
        self.socket = self.directory / 'rpc.sock'
        self.responses = {}
        relay = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                self.connection.settimeout(2)
                try:
                    line = self.rfile.readline(65_537)
                    require(len(line) <= 65_536 and line.endswith(b'\n'), 'REQUEST_TOO_LARGE', 'Use a bounded JSON request')
                    request = json.loads(line)
                    result = relay.dispatch(request)
                except (OrchiError, OSError, ValueError, TypeError, KeyError, ValidationError) as exc:
                    result = {'ok': False, 'code': getattr(exc, 'code', 'INVALID_REQUEST'), 'message': str(exc)}
                try:
                    self.wfile.write(json.dumps(result, ensure_ascii=False).encode() + b'\n')
                except (OSError, BrokenPipeError):
                    pass  # A stopped client cannot turn an accepted operation into another ticket.

        self.server = socketserver.UnixStreamServer(str(self.socket), Handler)
        self.socket.chmod(0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .05}, daemon=True)

    def dispatch(self, request: dict) -> dict:
        require(isinstance(request, dict) and set(request) == {'token', 'id', 'operation', 'arguments'},
                'INVALID_REQUEST', 'Use only the ticket channel envelope')
        require(isinstance(request['token'], str) and hmac.compare_digest(request['token'], self.token),
                'CHANNEL_DENIED', 'Invalid ticket channel capability')
        rid = request['id']
        require(isinstance(rid, str) and 1 <= len(rid) <= 80, 'INVALID_REQUEST', 'Bounded request ID required')
        fingerprint = json.dumps({k:v for k,v in request.items() if k != 'token'}, sort_keys=True)
        if rid in self.responses:
            old, result = self.responses[rid]
            require(fingerprint == old, 'REQUEST_ID_REUSED', 'Request ID is already bound to different arguments')
            return result
        require(len(self.responses) < 256, 'CHANNEL_BUDGET', 'A foreground phase allows at most 256 distinct requests')
        args = request['arguments']
        require(isinstance(args, dict), 'INVALID_REQUEST', 'Arguments must be an object')
        try:
            if request['operation'] == 'read':
                require(set(args) <= {'path','view','content_hash','start_line','end_line','consistency'} and 'path' in args,
                        'INVALID_REQUEST', 'Only exact source-read arguments are accepted')
                value = self.engine.ticket_read(self.ticket_id, args['path'], **{k:v for k,v in args.items() if k != 'path'})
            elif request['operation'] == 'scope':
                require(self.phase == 'execute', 'READINESS_REQUIRED', 'Preparation may only read exact sources')
                value = self.engine.acquire_scope(self.ticket_id, args)
            else:
                raise OrchiError('CHANNEL_OPERATION_DENIED', 'Only read and bounded scope acquisition are available')
            result = {'ok': True, 'result': value}
        except (OrchiError, OSError, ValueError, TypeError, KeyError, ValidationError) as exc:
            result = {'ok': False, 'code': getattr(exc, 'code', 'INVALID_REQUEST'), 'message': str(exc)}
        self.responses[rid] = (fingerprint, result)
        return result

    def __enter__(self):
        self.thread.start()
        return self

    def environment(self) -> dict:
        import sys
        return {'ORCHI_CHANNEL_SOCKET': str(self.socket), 'ORCHI_CHANNEL_TOKEN': self.token,
                'ORCHI_WORKER_REQUEST': str(Path(__file__).resolve().parents[1] / 'worker_request.py'),
                'ORCHI_WORKER_PYTHON': sys.executable}

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        shutil.rmtree(self.directory)
