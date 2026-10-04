import socket
import threading
import time
import unittest
from unittest.mock import patch
import inspect_lisp as m

class Tests(unittest.TestCase):
    def test_malformed_strings_rejected(self):
        for value in ['"unterminated', '(:ok "unterminated)', '"escaped' + chr(92) + '"']:
            with self.assertRaises(ValueError): m.parse(value)
    def test_absolute_deadline(self):
        c=m.Client.__new__(m.Client)
        c.sock=unittest.mock.Mock()
        with self.assertRaises(TimeoutError): c.exact(1, time.monotonic()-1)
        c.sock.recv.assert_not_called()
    def test_context_change_rejected(self):
        c=m.Client.__new__(m.Client)
        c.pid=1; c.expected=('exe','1',1); c.protocol='slynk'; c.serial=0
        c.sock=unittest.mock.Mock(); c.events=[]
        c.receive=unittest.mock.Mock(return_value=[m.Symbol(':debug-return'),3,1])
        with patch.object(m,'identity',return_value=c.expected):
            with self.assertRaisesRegex(ValueError,'context changed'): c.rpc('debugger-info-for-emacs', thread=3)
    def test_parse_data(self):
        self.assertEqual(m.parse('(:return (:ok (:pid 42 :name "hello \\"Lisp\\"")) 1)'), [':return', [':ok', [':pid',42,':name','hello "Lisp"']],1])
    def test_reader_forms_rejected(self):
        for value in ['#.(quit)', '(1 . 2)', '(a', 'a b', '(' * 70 + ')' * 70]:
            with self.assertRaises(ValueError): m.parse(value)
    def test_redacts_nested_debug_evidence(self):
        value = {'debugger': [{'state': ['password=hunter2', [m.Symbol(':name'), 'private']]}]}
        output = m.redact_output(value)
        self.assertNotIn('hunter2', str(output)); self.assertNotIn('private', str(output))
        self.assertIn(':name', str(output))
    def test_mutation_not_allowed(self):
        c = m.Client.__new__(m.Client)
        with self.assertRaises(ValueError): c.rpc('eval')
        with self.assertRaises(ValueError): c.rpc('invoke-nth-restart')
        with self.assertRaises(ValueError): c.rpc('debugger-info-for-emacs')
    def test_oversize_frame_rejected(self):
        a,b = socket.socketpair()
        c=m.Client.__new__(m.Client); c.sock=a
        try:
            b.sendall(b'ffffff')
            with self.assertRaises(ValueError): c.receive()
        finally: a.close(); b.close()
    def test_fragmented_utf8_frame(self):
        a,b=socket.socketpair(); c=m.Client.__new__(m.Client); c.sock=a
        wire='(:ok "λ")'.encode(); raw=f'{len(wire):06x}'.encode()+wire
        worker=threading.Thread(target=lambda: [b.sendall(bytes([v])) for v in raw]); worker.start()
        try: self.assertEqual(c.receive(), [':ok', 'λ'])
        finally: worker.join(); a.close(); b.close()
    def test_wrong_pid_rejected(self):
        fake=unittest.mock.Mock()
        with patch.object(m, 'verify_listener', return_value=('exe','1',1000)), patch.object(m.socket,'create_connection',return_value=fake), patch.object(m.Client,'rpc',return_value=[m.Symbol(':pid'),12]):
            with self.assertRaisesRegex(ValueError,'PID mismatch'): m.Client(13,4009)
        fake.close.assert_called_once()
    def test_process_changed_rejected(self):
        fake=unittest.mock.Mock()
        with patch.object(m, 'verify_listener', return_value=('exe','1',1000)), patch.object(m.socket,'create_connection',return_value=fake), patch.object(m.Client,'rpc',return_value=[m.Symbol(':pid'),13]), patch.object(m,'identity',return_value=('exe','2',1000)):
            with self.assertRaisesRegex(ValueError,'identity changed'): m.Client(13,4009)
        fake.close.assert_called_once()

if __name__ == '__main__': unittest.main()
