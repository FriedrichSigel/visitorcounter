"""
test_lora_transmitter.py — formaler Testfile für lora_transmitter.py.
Braucht keine Hardware, keine externen Pakete außer der Standardbibliothek.

Nutzung:
    python test_lora_transmitter.py

Bei Erfolg: "ALLE TESTS BESTANDEN" (unittest-Zusammenfassung). Bei einem
Fehler: AssertionError mit Zeilennummer, wie bei jedem unittest-Fehlschlag.

Für Tests mit dem echten Sonel-Gerät siehe stattdessen
lora_hardware_probe.py — das ist ein Diagnose-Skript für echte Hardware,
kein automatisierter Test wie dieser hier.
"""

import os
import tempfile
import unittest

from lora_transmitter import (
    encode_report, decode_report, LoRaReporter, DummyTransport, build_transport,
    MESSAGE_TYPE_AGGREGATE_REPORT,
)


class TestEncodeDecodeRoundTrip(unittest.TestCase):
    def test_basic_round_trip(self):
        counts = {"person": {"in": 12, "out": 5}, "car": {"in": 3, "out": 3}}
        payload = encode_report(counts, interval_minutes=10, timestamp=1751700000)
        decoded = decode_report(payload)

        self.assertEqual(decoded["counts"]["person"], {"in": 12, "out": 5})
        self.assertEqual(decoded["counts"]["car"], {"in": 3, "out": 3})
        self.assertEqual(decoded["interval_minutes"], 10)
        self.assertEqual(decoded["timestamp"], 1751700000)

    def test_zero_classes_are_omitted(self):
        counts = {"person": {"in": 1, "out": 0}, "bicycle": {"in": 0, "out": 0}}
        payload = encode_report(counts, interval_minutes=10)
        decoded = decode_report(payload)
        self.assertNotIn("bicycle", decoded["counts"])
        self.assertIn("person", decoded["counts"])

    def test_empty_report_is_seven_bytes(self):
        payload = encode_report({}, interval_minutes=10)
        self.assertEqual(len(payload), 7)
        decoded = decode_report(payload)
        self.assertEqual(decoded["counts"], {})

    def test_message_type_byte(self):
        payload = encode_report({}, interval_minutes=10)
        self.assertEqual(payload[0], MESSAGE_TYPE_AGGREGATE_REPORT)

    def test_unknown_message_type_raises(self):
        payload = bytearray(encode_report({}, interval_minutes=10))
        payload[0] = 0x99
        with self.assertRaises(ValueError):
            decode_report(bytes(payload))

    def test_saturation_at_255(self):
        counts = {"person": {"in": 300, "out": 0}}
        payload = encode_report(counts, interval_minutes=10)
        decoded = decode_report(payload)
        self.assertEqual(decoded["counts"]["person"]["in"], 255)

    def test_payload_too_short_raises(self):
        with self.assertRaises(ValueError):
            decode_report(b"\x01\x02")


class TestPayloadSizeBudget(unittest.TestCase):
    def test_max_size_all_classes_fits_smallest_lorawan_payload(self):
        all_counts = {label: {"in": 99, "out": 88} for label in
                      ["person", "bicycle", "car", "motorcycle", "bus", "truck"]}
        payload = encode_report(all_counts, interval_minutes=15)
        self.assertEqual(len(payload), 25)
        # SF12 in EU868 erlaubt je nach Region/Header ca. 51-59 Byte Nutzlast —
        # 25 Byte lässt auch bei der kleinsten Spreizfaktor-Konfiguration
        # noch deutlich Luft.
        self.assertLess(len(payload), 51)


class TestLoRaReporter(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._old_cwd = os.getcwd()
        os.chdir(self._tmpdir)

    def tearDown(self):
        os.chdir(self._old_cwd)

    def test_record_event_aggregates_correctly(self):
        reporter = LoRaReporter(DummyTransport(), interval_minutes=10)
        reporter.record_event("person", "in")
        reporter.record_event("person", "in")
        reporter.record_event("person", "out")
        reporter.record_event("car", "in")

        self.assertEqual(reporter._counts["person"], {"in": 2, "out": 1})
        self.assertEqual(reporter._counts["car"], {"in": 1, "out": 0})

    def test_invalid_direction_is_ignored(self):
        reporter = LoRaReporter(DummyTransport(), interval_minutes=10)
        reporter.record_event("person", "A->B")  # kein "in"/"out" -> ignorieren
        self.assertEqual(reporter._counts, {})

    def test_unknown_class_is_ignored(self):
        reporter = LoRaReporter(DummyTransport(), interval_minutes=10)
        reporter.record_event("unbekannte_klasse", "in")
        self.assertEqual(reporter._counts, {})

    def test_send_and_reset_clears_counts(self):
        reporter = LoRaReporter(DummyTransport(), interval_minutes=10)
        reporter.record_event("person", "in")
        success = reporter.send_and_reset()
        self.assertTrue(success)
        self.assertEqual(reporter._counts, {})

    def test_send_and_reset_writes_log_file(self):
        log_path = "test_lora_outbox.log"
        reporter = LoRaReporter(DummyTransport(log_path=log_path), interval_minutes=10)
        reporter.record_event("person", "in")
        reporter.record_event("car", "out")
        reporter.send_and_reset()

        self.assertTrue(os.path.isfile(log_path))
        with open(log_path) as f:
            content = f.read()
        self.assertIn("'person': {'in': 1, 'out': 0}", content)
        self.assertIn("'car': {'in': 0, 'out': 1}", content)

    def test_empty_interval_still_sends_as_heartbeat(self):
        log_path = "test_lora_outbox.log"
        reporter = LoRaReporter(DummyTransport(log_path=log_path), interval_minutes=10)
        reporter.send_and_reset()
        self.assertTrue(os.path.isfile(log_path))
        with open(log_path) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)


class TestBuildTransport(unittest.TestCase):
    def test_dummy_transport(self):
        transport = build_transport("dummy")
        self.assertIsInstance(transport, DummyTransport)

    def test_unknown_transport_falls_back_to_dummy(self):
        transport = build_transport("does_not_exist")
        self.assertIsInstance(transport, DummyTransport)

    def test_serial_at_transport_requires_pyserial_or_real_port(self):
        # Ohne echtes Gerät/pyserial-Umgebung erwarten wir hier einen Fehler
        # beim Öffnen des Ports (kein Absturz mit unklarer Exception-Art) —
        # dieser Test dokumentiert nur das erwartete Verhalten ohne Hardware,
        # er beweist NICHT, dass die Kommunikation mit einem echten Gerät
        # funktioniert (siehe lora_hardware_probe.py dafür).
        with self.assertRaises(Exception):
            build_transport("serial_at", serial_port="/dev/nonexistent_port_for_test")


if __name__ == "__main__":
    unittest.main(verbosity=2)
