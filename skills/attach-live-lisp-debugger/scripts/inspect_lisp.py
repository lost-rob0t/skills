#!/usr/bin/env python3
"""Bounded, loopback-only Slynk/Swank inspector. No arbitrary eval or restart API."""
import argparse
import json
import os
from pathlib import Path
import re
import select
import socket
import time

MAX_FRAME = 262144

class Symbol(str):
    pass

def parse(text):
    """Parse the protocol's data subset; never invoke a Lisp/Python reader/eval."""
    tokens = []
    cursor = 0
    while cursor < len(text):
        if text[cursor].isspace(): cursor += 1; continue
        if text[cursor] in '()':
            tokens.append(text[cursor]); cursor += 1; continue
        if text[cursor] == '"':
            begin = cursor
            cursor += 1
            while cursor < len(text):
                if text[cursor] == "\\":
                    cursor += 2
                elif text[cursor] == '"':
                    cursor += 1
                    tokens.append(text[begin:cursor])
                    break
                else: cursor += 1
            else: raise ValueError('Unclosed string')
            continue
        begin = cursor
        while cursor < len(text) and not text[cursor].isspace() and text[cursor] not in '()"':
            cursor += 1
        tokens.append(text[begin:cursor])
    position = 0
    def read(depth=0):
        nonlocal position
        if depth > 64 or position >= len(tokens):
            raise ValueError('Invalid/deep protocol expression')
        token = tokens[position]; position += 1
        if token == '(':
            result = []
            while position < len(tokens) and tokens[position] != ')':
                result.append(read(depth + 1))
            if position >= len(tokens): raise ValueError('Unclosed list')
            position += 1
            return result
        if token == ')': raise ValueError('Unexpected closing parenthesis')
        if token.startswith('"'):
            if len(token) < 2 or not token.endswith('"'): raise ValueError('Unclosed string')
            return re.sub(r'\\(.)', r'\1', token[1:-1], flags=re.S)
        if re.fullmatch(r'-?\d+', token): return int(token)
        if token.lower() == 'nil': return None
        if token.startswith(('#', "'", '`', ',')) or token == '.':
            raise ValueError('Unsupported reader syntax')
        return Symbol(token.lower())
    result = read()
    if position != len(tokens): raise ValueError('Trailing protocol expression')
    return result

def identity(pid):
    base = Path('/proc') / str(pid)
    fields = (base / 'stat').read_text().rsplit(')', 1)[1].split()
    return (os.readlink(base / 'exe'), fields[19], base.stat().st_uid)

def verify_listener(pid, port):
    expected = identity(pid)
    if expected[2] != os.getuid(): raise ValueError('Process is not owned by current user')
    inodes = set()
    for fd in (Path('/proc') / str(pid) / 'fd').iterdir():
        try:
            link = os.readlink(fd)
            if link.startswith('socket:['): inodes.add(link[8:-1])
        except FileNotFoundError:
            pass
    found = False
    for line in Path('/proc/net/tcp').read_text().splitlines()[1:]:
        fields = line.split()
        host, p = fields[1].split(':')
        if int(p, 16) == port and fields[3] == '0A' and fields[9] in inodes:
            if host != '0100007F': raise ValueError('Endpoint is not exclusively IPv4 loopback')
            found = True
    if not found: raise ValueError('Cannot verify exact PID owns 127.0.0.1 listener')
    return expected

class Client:
    def __init__(self, pid, port, protocol='slynk', timeout=5):
        self.pid, self.protocol, self.serial = pid, protocol, 0
        self.expected = verify_listener(pid, port)
        self.sock = socket.create_connection(('127.0.0.1', port), timeout)
        self.sock.settimeout(timeout)
        self.events = []
        try:
            info = self.rpc('connection-info')
            if not isinstance(info, list) or len(info) % 2: raise ValueError('Invalid identity reply')
            pairs = dict(zip(info[::2], info[1::2]))
            if pairs.get(':pid') != pid: raise ValueError('Debugger PID mismatch')
            if identity(pid) != self.expected: raise ValueError('Process identity changed')
            self.info = info
        except BaseException:
            self.close(); raise
    def close(self):
        self.sock.close()
    def exact(self, n, deadline):
        data = b''
        while len(data) < n:
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise TimeoutError('Absolute frame deadline exceeded')
            self.sock.settimeout(remaining)
            chunk = self.sock.recv(n - len(data))
            if not chunk: raise EOFError('Debugger disconnected')
            data += chunk
        return data
    def receive(self, deadline=None):
        deadline = deadline if deadline is not None else time.monotonic() + 5
        header = self.exact(6, deadline)
        if not re.fullmatch(b'[0-9a-fA-F]{6}', header): raise ValueError('Bad frame header')
        n = int(header, 16)
        if n > MAX_FRAME: raise ValueError('Protocol frame exceeds evidence limit')
        return parse(self.exact(n, deadline).decode('utf-8'))
    def rpc(self, method, thread=None, frames=20):
        if method not in ('connection-info', 'list-threads', 'debugger-info-for-emacs'):
            raise ValueError('RPC is not on inspection allowlist')
        if method == 'debugger-info-for-emacs' and (type(thread) is not int or thread < 0):
            raise ValueError('Debugger inspection requires observed thread ID')
        if not 1 <= frames <= 50: raise ValueError('Frame limit must be 1..50')
        if identity(self.pid) != self.expected: raise ValueError('Process identity changed')
        self.serial += 1
        args = f' 0 {frames}' if method == 'debugger-info-for-emacs' else ''
        form = f'(:emacs-rex ({self.protocol}:{method}{args}) "CL-USER" {thread if thread is not None else "t"} {self.serial})'
        data = form.encode(); self.sock.sendall(f'{len(data):06x}'.encode() + data)
        deadline = time.monotonic() + 10
        for _ in range(100):
            if time.monotonic() > deadline: raise TimeoutError('RPC deadline exceeded')
            event = self.receive(deadline)
            if method == 'debugger-info-for-emacs' and isinstance(event, list) and len(event) >= 2 and event[0] in (':debug-return', ':debug') and event[1] == thread:
                raise ValueError('Debugger context changed during inspection; discard snapshot')
            if isinstance(event, list) and len(event) == 3 and event[0] == ':return' and event[2] == self.serial:
                status = event[1]
                if not isinstance(status, list) or status[0] != ':ok': raise ValueError('RPC aborted')
                return status[1]
            self.events.append(event)
        raise ValueError('Too many unsolicited debugger messages')

def redact(value, details=False):
    # By default suppress *every* server string (names, paths, conditions and arguments).
    if isinstance(value, Symbol): return str(value)
    if isinstance(value, str):
        if not details: return '[server string omitted]'
        value = re.sub(r'(?i)(password|secret|token|api[_-]?key|authorization)\s*[:=]\s*[^\s,;)]+', r'\1=[REDACTED]', value)
        return value[:1000]
    if isinstance(value, list): return [redact(x, details) for x in value[:100]]
    if isinstance(value, dict): return {k: redact(v, details) for k, v in value.items()}
    return value

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid', type=int, required=True); p.add_argument('--port', type=int, required=True)
    p.add_argument('--protocol', choices=['slynk', 'swank'], default='slynk')
    p.add_argument('--authorized-attach', action='store_true', required=True)
    p.add_argument('--watch-seconds', type=float, default=0)
    p.add_argument('--disconnect-approved', action='store_true', required=True,
                   help='Owner approved debugger disconnect behavior, including active conditions')
    p.add_argument('--include-details', action='store_true', help='Local-only strings; manually redact before sharing')
    args = p.parse_args()
    if not 0 <= args.watch_seconds <= 60: p.error('watch-seconds must be 0..60')
    client = Client(args.pid, args.port, args.protocol)
    try:
        output = {'identity': client.info, 'threads': client.rpc('list-threads'), 'debugger': []}
        deadline = time.monotonic() + args.watch_seconds
        observed = 0
        while True:
            while client.events:
                event = client.events.pop(0)
                observed += 1
                if observed > 100: raise ValueError('Session event limit exceeded')
                if isinstance(event, list) and len(event) >= 3 and event[0] == ':debug':
                    key = (event[1], event[2])
                    stale = any(isinstance(e, list) and len(e) >= 3 and e[0] == ':debug-return' and e[1:3] == list(key) for e in client.events)
                    if not stale:
                        output['debugger'].append({'thread': key[0], 'event_level': key[1],
                            'context_note': 'Level was observed in event; snapshot is not atomic with that event',
                            'state': client.rpc('debugger-info-for-emacs', thread=key[0])})
            remaining = deadline - time.monotonic()
            if remaining <= 0: break
            if select.select([client.sock], [], [], remaining)[0]:
                client.sock.settimeout(5)
                client.events.append(client.receive(deadline))
        print(json.dumps(redact_output(output, args.include_details), indent=2))
    finally:
        client.close()

def redact_output(value, details=False):
    if isinstance(value, dict): return {k: redact_output(v, details) for k, v in value.items()}
    return redact(value, details)

if __name__ == '__main__':
    main()
