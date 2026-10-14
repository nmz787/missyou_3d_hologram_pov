"""Wire-level regression checks against deterministic localhost display stand-ins.

No real display, Android phone or external network is used. Fixtures use APK
wire constants independently of povbin.device's implementation.
"""
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from povbin.device import DeviceClient, DeviceError

END = b'a4a8c2e3'
HEARTBEAT = b'c31c38abca4a8c2e3'


def notification(names, tail=b'00711'):
    records = []
    for index, name in enumerate(names):
        encoded = name.encode('gbk')
        records.append(f'{len(encoded) + 5:02d}{index:02d}'.encode() + b'---' + encoded)
    return b'c30c38abc' + b''.join(records) + tail + END


def recv_exact(conn, count):
    data = bytearray()
    while len(data) < count:
        chunk = conn.recv(count - len(data))
        if not chunk:
            raise AssertionError(f'Peer closed after {len(data)} of {count} bytes')
        data.extend(chunk)
    return bytes(data)


class TCPStandIn:
    """Local server that reports background assertions in the owning test."""
    def __init__(self, handler):
        self.handler = handler
        self.errors = []
        self.stopping = threading.Event()
        self.listener = socket.socket()
        self.listener.bind(('127.0.0.1', 0))
        self.port = self.listener.getsockname()[1]
        self.listener.listen()
        self.listener.settimeout(0.1)
        self.connections = []
        self.workers = []
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        while not self.stopping.is_set():
            try:
                conn, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            self.connections.append(conn)
            conn.settimeout(2)
            worker = threading.Thread(target=self.handle, args=(conn,), daemon=True)
            self.workers.append(worker)
            worker.start()

    def handle(self, conn):
        try:
            with conn:
                self.handler(conn)
        except (ConnectionResetError, BrokenPipeError, OSError) as exc:
            if not self.stopping.is_set():
                self.errors.append(exc)
        except Exception as exc:
            self.errors.append(exc)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stopping.set()
        self.listener.close()
        for conn in self.connections:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.thread.join(2)
        for worker in self.workers:
            worker.join(2)
        if exc[0] is None and self.errors:
            raise self.errors[0]


def control_handler(names, chunks=None, commands=None, tail=b'00711'):
    def handle(conn):
        pending = b''
        while True:
            data = conn.recv(4096)
            if not data:
                return
            pending += data
            while END in pending:
                end = pending.index(END) + len(END)
                command, pending = pending[:end], pending[end:]
                if commands is not None:
                    commands.append(command)
                if command == HEARTBEAT:
                    response = notification(names, tail)
                    parts = chunks(response) if chunks else [response]
                    for part in parts:
                        conn.sendall(part)
                        if chunks:
                            time.sleep(0.005)
    return handle


class LegacyWireTests(unittest.TestCase):
    def client(self, control, upload=None, timeout=0.5):
        return DeviceClient(host='127.0.0.1', protocol='legacy', timeout=timeout,
                            control_port=control.port,
                            upload_port=upload.port if upload else 1)

    def test_fragmented_notification_keeps_all_names_and_gbk(self):
        names = ['00_B.bin', '13_example.bin', '01春节.bin']
        with TCPStandIn(control_handler(names, lambda b: [b[:2], b[2:11], b[11:b.index('春'.encode('gbk')) + 1], b[b.index('春'.encode('gbk')) + 1:-3], b[-3:]])) as control:
            with self.client(control) as client:
                result = client.files()['files']
                self.assertEqual([f['name'] for f in result], names)
                self.assertEqual([f['index'] for f in result], [0, 1, 2])

    def test_coalesced_notifications_do_not_create_spurious_records(self):
        names = ['00_B.bin', '13_example.bin']
        with TCPStandIn(control_handler(names, lambda b: [b + b])) as control:
            with self.client(control) as client:
                self.assertEqual([f['name'] for f in client.files()['files']], names)

    def test_control_messages_use_device_index_not_filename_prefix(self):
        commands = []
        with TCPStandIn(control_handler(['00_B.bin', '13_example.bin'], commands=commands)) as control:
            with self.client(control) as client:
                client.play('13_example.bin')
                client.pause()
                client.resume()
                client.next()
                client.previous()
                client.power(False)
                client.loop(True)
            for worker in control.workers:
                worker.join(1)
            # Device list index1 differs from the filename's leading13.
            self.assertIn(b'c31c40abe01a4a8c2e3', commands)
            for expected in [b'c31c34abca4a8c2e3', b'c31c35abca4a8c2e3',
                             b'c31c32abca4a8c2e3', b'c31c33abca4a8c2e3',
                             b'c31c89abca4a8c2e3', b'c31c36abca4a8c2e3']:
                self.assertIn(expected, commands)

    def test_recorded_firmware_length_bug_salvages_later_files_and_model(self):
        # Regression fixture for an observed malformed directory; names generalized.
        # Record 6 advertises length16 but overlaps the length13/index12 row.
        # APK stops at this record and fails to reach the later entry at device index 15.
        packet = (b'c30c38arh130101.00_B.bin170202.01DEMO~1.bin'
                  b'140303.01_AB.bin170404.02DEMO~1.bin170505.03DEMO~1.bin'
                  b'160606.04in131212.10AB.bin171313.11DEMO~1.bin'
                  b'171414.12DEMO~1.bin171515.13_DEM~1.bin15H711a4a8c2e3')
        def handle(conn):
            while True:
                command = conn.recv(4096)
                if not command:
                    return
                conn.sendall(packet)
        with TCPStandIn(handle) as control:
            with self.client(control) as client:
                status = client.status()
                self.assertFalse(status['complete'])
                self.assertTrue(status['issues'])
                self.assertEqual(status['model'], 'F-MINI11')
                self.assertEqual(status['current_index'], 15)
                self.assertTrue(status['is_playing'])
                entries = client.files()['files']
                later_file = next(f for f in entries if f['name'] == '13_DEM~1.bin')
                self.assertEqual(later_file['index'], 15)
                self.assertIn('10AB.bin', [f['name'] for f in entries])
                self.assertNotIn('04in131212.', [f['name'] for f in entries])

    def test_unknown_model_does_not_hide_otherwise_valid_files(self):
        names = ['13_example.bin', '01春节.bin']
        with TCPStandIn(control_handler(names, tail=b'00H911')) as control:
            with self.client(control) as client:
                status = client.status()
                self.assertTrue(status['complete'])
                self.assertIsNone(status['model'])
                self.assertEqual(status['model_flag'], 'H9')
                self.assertEqual([f['name'] for f in client.files()['files']], names)

    def test_incomplete_listing_blocks_unapproved_upload(self):
        def handle(conn):
            while True:
                data = conn.recv(4096)
                if not data:
                    return
                conn.sendall(b'c30c38abc1300---00_B.binXX01---13_example.bin00711' + END)
        touched = threading.Event()
        def unexpected_upload(conn):
            touched.set()
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            source = Path(folder) / 'NEW.BIN'
            source.write_bytes(b'content')
            control = stack.enter_context(TCPStandIn(handle))
            upload_server = stack.enter_context(TCPStandIn(unexpected_upload))
            with self.client(control, upload_server) as client:
                with self.assertRaises(DeviceError):
                    client.upload(source)
            self.assertFalse(touched.wait(0.05), 'Incomplete listing must block before opening upload socket')

    def test_upload_matches_full_native_frame_layout_and_ack_windows(self):
        payload = bytes((i * 17 + 3) % 256 for i in range(1440 * 41 + 23))
        name = '01春节.bin'
        encoded = name.encode('gbk')
        names = ['00_B.bin']
        seen = {'acks': []}
        def upload(conn):
            info = recv_exact(conn, len(encoded) + 21)
            self.assertEqual(info[:8], b'd31d66DF')
            self.assertEqual(info[8], len(encoded) + 61)
            self.assertEqual(int.from_bytes(info[9:13], 'big'), 42 * 1440)
            self.assertEqual(info[13:-8], encoded)
            self.assertEqual(info[-8:], END)
            for part in [b'd30', b'd66', END[:3], END[3:]]:
                conn.sendall(part)
            received = bytearray()
            for block in range(42):
                frame = recv_exact(conn, 1460)
                self.assertEqual(frame[:9], b'd31d88JMP')
                self.assertEqual(frame[-11:], b'000' + END)
                received.extend(frame[9:-11])
                if (block + 1) % 20 == 0 or block == 41:
                    seen['acks'].append(block + 1)
                    conn.sendall(b'd30d88' + END)
            self.assertEqual(bytes(received[:len(payload)]), payload)
            self.assertEqual(bytes(received[len(payload):]), bytes(1417))
            self.assertEqual(recv_exact(conn, 17), b'd31d88DEF' + END)
            names.append(name)
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            source = Path(folder) / 'source.bin'
            source.write_bytes(payload)
            control = stack.enter_context(TCPStandIn(control_handler(names)))
            upload_server = stack.enter_context(TCPStandIn(upload))
            with self.client(control, upload_server, timeout=1) as client:
                result = client.upload(source, name=name)
                self.assertEqual(result['bytes'], len(payload))
                self.assertEqual(result['blocks'], 42)
                self.assertEqual(result['padded_bytes'], 60480)
                self.assertTrue(result['listing_stable'])
                self.assertFalse(result['verified'])
                self.assertFalse(result['content_verified'])
            self.assertEqual(seen['acks'], [20, 40, 42])

    def test_upload_missing_or_wrong_data_ack_fails_without_completion(self):
        for reply in [b'', b'd30d66' + END]:
            with self.subTest(reply=reply), tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
                source = Path(folder) / 'NEW.BIN'
                source.write_bytes(b'last block')
                received = []
                def upload(conn):
                    recv_exact(conn, len(b'NEW.BIN') + 21)
                    conn.sendall(b'd30d66' + END)
                    recv_exact(conn, 1460)
                    if reply:
                        conn.sendall(reply)
                    conn.settimeout(0.7)
                    try:
                        received.append(conn.recv(4096))
                    except socket.timeout:
                        received.append(b'')
                control = stack.enter_context(TCPStandIn(control_handler([])))
                upload_server = stack.enter_context(TCPStandIn(upload))
                with self.client(control, upload_server, timeout=0.1) as client:
                    with self.assertRaises(DeviceError):
                        client.upload(source)
                for worker in upload_server.workers:
                    worker.join(1)
                self.assertFalse(any(b'd31d88DEF' in item for item in received))

    def test_adb_transport_uses_nonpty_shell_and_binary_duplex_pipes(self):
        # Replace only the adb launcher with a local subprocess TCP bridge.
        # This exercises real binary pipe I/O without invoking adb or a phone.
        real_popen = subprocess.Popen
        commands = []
        with TCPStandIn(control_handler(['01春节.bin', '13_example.bin'])) as control:
            bridge = """
import os, select, socket
s = socket.create_connection(('127.0.0.1', LOCAL_PORT))
while True:
    ready, _, _ = select.select([0, s], [], [], 2)
    if not ready: continue
    if 0 in ready:
        chunk = os.read(0, 8192)
        if not chunk: break
        s.sendall(chunk)
    if s in ready:
        chunk = s.recv(8192)
        if not chunk: break
        os.write(1, chunk)
s.close()
""".replace('LOCAL_PORT', str(control.port))
            def launch(command, *args, **kwargs):
                commands.append(list(command))
                return real_popen([sys.executable, '-u', '-c', bridge], *args, **kwargs)
            with patch('subprocess.Popen', side_effect=launch):
                with DeviceClient(host='127.0.0.1', protocol='legacy',
                                  adb_serial='TEST-SERIAL', control_port=control.port,
                                  timeout=1) as client:
                    entries = client.files()['files']
                    self.assertEqual([f['name'] for f in entries], ['01春节.bin', '13_example.bin'])
            self.assertTrue(commands)
            command = commands[0]
            self.assertEqual(command[:3], ['adb', '-s', 'TEST-SERIAL'])
            self.assertIn('shell', command)
            self.assertIn('-T', command)
            self.assertNotIn('exec-out', command)
            self.assertTrue(any('nc' in item for item in command))

    def test_existing_destination_refused_before_upload_socket(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'TAKEN.BIN'
            source.write_bytes(b'content')
            with TCPStandIn(control_handler(['TAKEN.BIN'])) as control:
                with self.client(control) as client:
                    with self.assertRaises(FileExistsError):
                        client.upload(source)

    def test_control_polls_until_delayed_state_is_observed(self):
        state = {'paused_at': None}
        def handle(conn):
            pending = b''
            while True:
                data = conn.recv(4096)
                if not data:
                    return
                pending += data
                while END in pending:
                    end = pending.index(END) + len(END)
                    cmd, pending = pending[:end], pending[end:]
                    if cmd == b'c31c34abc' + END:
                        state['paused_at'] = time.monotonic() + 0.95
                    if cmd == HEARTBEAT:
                        paused = state['paused_at'] is not None and time.monotonic() >= state['paused_at']
                        conn.sendall(notification(['CD.BIN'], tail=b'00H710' if paused else b'00H711'))
        with TCPStandIn(handle) as control:
            with self.client(control, timeout=1) as client:
                client.status()
                result = client.pause()
                self.assertTrue(result['requested_state_observed'])
                self.assertFalse(result['status']['is_playing'])
                self.assertFalse(result['acknowledged'])

    def test_unconfirmed_upload_status_aborts_before_data(self):
        received = []
        def upload(conn):
            recv_exact(conn, len(b'NEW.BIN') + 21)
            conn.sendall(b'd30d66DEJ0000' + END)
            received.append(conn.recv(1460))
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            source = Path(folder) / 'NEW.BIN'
            source.write_bytes(b'content')
            control = stack.enter_context(TCPStandIn(control_handler([])))
            upload_server = stack.enter_context(TCPStandIn(upload))
            with self.client(control, upload_server) as client:
                with self.assertRaisesRegex(DeviceError, 'firmware meaning.*unknown'):
                    client.upload(source)
            for worker in upload_server.workers:
                worker.join(1)
            self.assertEqual(received, [b''])

    def test_format_observes_complete_empty_directory(self):
        names = ['OLD.BIN']
        def handle(conn):
            pending = b''
            while True:
                data = conn.recv(4096)
                if not data:
                    return
                pending += data
                while END in pending:
                    end = pending.index(END) + len(END)
                    cmd, pending = pending[:end], pending[end:]
                    if cmd == b'c31c88abc' + END:
                        names.clear()
                    if cmd == HEARTBEAT:
                        conn.sendall(notification(names))
        with TCPStandIn(handle) as control:
            with self.client(control) as client:
                client.status()
                result = client.format_card()
                self.assertTrue(result['directory_empty_observed'])
                self.assertTrue(result['status']['complete'])
                self.assertEqual(result['status']['files'], [])


class HTTPStandIn:
    def __init__(self, respond):
        self.calls = []
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                owner.dispatch(self, b'')
            def do_POST(self):
                owner.dispatch(self, self.rfile.read(int(self.headers.get('Content-Length', '0'))))
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_port
        self.respond = respond
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def dispatch(self, handler, body):
        self.calls.append((handler.command, handler.path, dict(handler.headers), body))
        reply = json.dumps(self.respond(handler.command, handler.path, body)).encode()
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Content-Length', str(len(reply)))
        handler.end_headers()
        handler.wfile.write(reply)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)


class HTTPWireTests(unittest.TestCase):
    def client(self, server):
        return DeviceClient(host='127.0.0.1', protocol='http', http_port=server.port,
                            timeout=0.5)

    def test_gbk_filename_list_play_delete_and_multipart_upload(self):
        name = '01春节.bin'
        encoded = '3031b4babdda2e62696e'
        files = [name]
        def respond(method, path, body):
            if path == '/info':
                return {'code': 0, 'model': 'F-MINI11'}
            if path == '/DCIM':
                return {'code': 0, 'files': [n.encode('gbk').hex() for n in files]}
            if path == '/DCIM/' + encoded + '?act=rm':
                files.remove(name)
            if path == '/DCIM/upload':
                files.append('新片.bin')
            return {'code': 0}
        with HTTPStandIn(respond) as server, tempfile.TemporaryDirectory() as folder:
            payload = b'\x00\xffbin payload\r\n--not-a-boundary'
            source = Path(folder) / 'source.bin'
            source.write_bytes(payload)
            with self.client(server) as client:
                self.assertEqual(client.files()['files'][0]['name'], name)
                client.play(name)
                client.delete(name)
                result = client.upload(source, name='新片.bin')
                self.assertTrue(result['listing_stable'])
                self.assertFalse(result['verified'])
            paths = [call[1] for call in server.calls]
            self.assertIn('/DCIM/' + encoded + '?act=play', paths)
            self.assertIn('/DCIM/' + encoded + '?act=rm', paths)
            posts = [call for call in server.calls if call[0] == 'POST']
            self.assertEqual(len(posts), 1)
            _, path, headers, body = posts[0]
            self.assertEqual(path, '/DCIM/upload')
            self.assertIn('multipart/form-data', headers['Content-Type'])
            self.assertIn(b'name="name"', body)
            self.assertIn(b'\r\n\r\n' + '新片.bin'.encode('gbk').hex().encode() + b'\r\n', body)
            self.assertIn(b'name="file"', body)
            self.assertIn(b'filename="' + '新片.bin'.encode('gbk').hex().encode() + b'"', body)
            self.assertIn(b'Content-Type: application/octet-stream', body)
            self.assertIn(payload, body)

    def test_settings_parse_server_values_and_send_exact_key(self):
        def respond(method, path, body):
            if path == '/ctrl/get?k=all':
                return {'code': 0, 'data': [{'key': 'brightness', 'value': 50},
                                           {'key': 'volume', 'value': 20}]}
            return {'code': 0}
        with HTTPStandIn(respond) as server:
            with self.client(server) as client:
                settings = client.settings()
                self.assertEqual(settings['brightness'], 50)
                self.assertEqual(settings['volume'], 20)
                client.set_setting('brightness', 80)
            self.assertIn('/ctrl/set?brightness=80', [call[1] for call in server.calls])

    def test_code_one_setting_failure_is_not_reported_as_success(self):
        def respond(method, path, body):
            return {'code': 1, 'message': 'setting rejected'} if path.startswith('/ctrl/set') else {'code': 0}
        with HTTPStandIn(respond) as server:
            with self.client(server) as client:
                with self.assertRaises(DeviceError):
                    client.set_setting('brightness', 80)
            paths = [call[1] for call in server.calls]
            self.assertTrue(any(parse_qs(urlsplit(path).query).get('brightness') == ['80'] for path in paths))


if __name__ == '__main__':
    unittest.main()
