// ttn_payload_decoder.js
// Payload-Decoder fuer das 25-Byte-Zaehlformat (Version 1).
//
// Einsatz in TTN: Application > Payload formatters > Uplink > Custom Javascript.
// Derselbe Decoder ist die Referenz fuer den Network Server der Stadtwerke
// Potsdam (ChirpStack u. ae. nutzen dieselbe Signatur).
//
// Format (big endian) — muss exakt CountMessage.pack() in lora_transmitter.py
// entsprechen:
//   [0]     u8   version           (aktuell 1)
//   [1]     u8   sensor_id         (1..17 = Eingang, 99 = Testsensor)
//   [2..5]  u32  timestamp         (Unix UTC, Sekunden)
//   [6..7]  u16  count_in          (Eintritte im Intervall)
//   [8..9]  u16  count_out         (Austritte im Intervall)
//   [10..11]u16  count_total_in    (Eintritte seit Start)
//   [12..13]u16  count_total_out   (Austritte seit Start)
//   [14..15]u16  interval_s
//   [16]    u8   zone_count
//   [17]    u8   mode              (0=Linie, 1=ROI, 2=Mehrere Flaechen)
//   [18]    u8   status            (Bitfeld)
//   [19..20]u16  frames_processed
//   [21..24]u32  reserved

function decodeUplink(input) {
  var b = input.bytes;

  if (b.length !== 25) {
    return { errors: ["Erwartet 25 Byte, bekommen " + b.length] };
  }
  if (b[0] !== 1) {
    return { errors: ["Unbekannte Formatversion: " + b[0]] };
  }

  function u16(i) { return (b[i] << 8) | b[i + 1]; }
  function u32(i) { return ((b[i] << 24) | (b[i+1] << 16) | (b[i+2] << 8) | b[i+3]) >>> 0; }

  var modeNames = ["Linie", "ROI", "Mehrere Flaechen"];
  var status = b[18];

  return {
    data: {
      version:          b[0],
      sensor_id:        b[1],
      timestamp:        u32(2),
      time_iso:         new Date(u32(2) * 1000).toISOString(),
      count_in:         u16(6),
      count_out:        u16(8),
      count_total_in:   u16(10),
      count_total_out:  u16(12),
      interval_s:       u16(14),
      zone_count:       b[16],
      mode:             b[17],
      mode_name:        modeNames[b[17]] || ("unbekannt(" + b[17] + ")"),
      status_camera_ok: (status & 0x01) !== 0,
      status_accel_ok:  (status & 0x02) !== 0,
      status_config_ok: (status & 0x04) !== 0,
      status_buffered:  (status & 0x08) !== 0,
      frames_processed: u16(19)
    }
  };
}
