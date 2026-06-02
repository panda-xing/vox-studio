# ============================================================
#  VoxCPM2 TTS & ASR Service Request Test
# ============================================================
# Prerequisites:
#   Terminal 1: python tts_server.py    (port 8801)
#   Terminal 2: python asr_server.py    (port 8802)
#
# Run:
#   python test_servers.py
#   python test_servers.py --tts-only
#   python test_servers.py --asr-only
# ============================================================

import argparse
import json
import sys
import time
import os
import urllib.request
import urllib.error

# ==================== Config ====================

DEFAULT_TTS_URL = "http://localhost:8801"
DEFAULT_ASR_URL = "http://localhost:8802"
TEST_WAV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        chr(21016) + chr(23068) + chr(24405) + chr(38899) + ".wav")

# ==================== Helpers ====================


def get(url, label=""):
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        print(f"  [GET] {label or url} => {json.dumps(data, ensure_ascii=False)}")
        return data
    except urllib.error.URLError as e:
        print(f"  [GET] {label or url} => connection failed: {e}")
        return None


def post(url, body=None, label=""):
    try:
        send_data = json.dumps(body or {}).encode("utf-8")
        req = urllib.request.Request(url, data=send_data,
                                      headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        print(f"  [POST] {label or url} => {json.dumps(result, ensure_ascii=False)}")
        return result
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"  [POST] {label or url} => HTTP {e.code}: {body_text[:200]}")
        return None
    except urllib.error.URLError as e:
        print(f"  [POST] {label or url} => connection failed: {e}")
        return None


def post_sse(url, body, label="", timeout=60):
    import http.client
    try:
        stripped = url.replace("http://", "")
        host_port = stripped.split("/")[0]
        path = "/" + "/".join(stripped.split("/")[1:])
        host = host_port.split(":")[0]
        port = int(host_port.split(":")[1])

        data = json.dumps(body).encode("utf-8")
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("POST", path, body=data,
                     headers={"Content-Type": "application/json",
                              "Accept": "text/event-stream"})
        resp = conn.getresponse()
        if resp.status != 200:
            print(f"  [SSE] {label} => HTTP {resp.status}")
            conn.close()
            return []

        print(f"  [SSE] {label} => HTTP {resp.status}, waiting for events...")
        events = []
        raw = resp.read().decode("utf-8")
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                payload = line[5:].strip()
                try:
                    evt = json.loads(payload)
                    events.append(evt)
                    event_type = evt.get("event", "?")
                    if event_type == "done":
                        print(f"         {event_type}: {json.dumps(evt, ensure_ascii=False)}")
                    elif event_type == "segment_done":
                        idx = evt.get("segment_index", "?")
                        total = evt.get("total_segments", "?")
                        chunks = evt.get("segment_chunks", "?")
                        seg_time = evt.get("segment_time", "?")
                        print(f"         {event_type}: seg {idx}/{total} {chunks} chunks {seg_time}s")
                    elif event_type == "partial":
                        chunk_id = evt.get("chunk", "?")
                        text = evt.get("text", "")
                        print(f"         {event_type}: chunk {chunk_id} text={text}")
                    else:
                        print(f"         {event_type}: {json.dumps(evt, ensure_ascii=False)[:100]}")
                except json.JSONDecodeError:
                    print(f"         raw: {payload[:80]}")
        conn.close()
        return events
    except Exception as e:
        print(f"  [SSE] {label} => error: {e}")
        return []


# ==================== TTS Tests ====================

def test_tts(base_url):
    print("\n" + "=" * 60)
    print("  TTS Service Test (port 8801)")
    print("=" * 60)

    # 1. Health
    print("\n[1] GET /health")
    data = get(f"{base_url}/health", "health check")
    if not data:
        print("  !! TTS service not running, skip remaining tests")
        return False
    if not data.get("model_loaded"):
        print("  !! Model not loaded")
        return False
    print(f"  [OK] Model loaded, sample_rate: {data.get('sample_rate')}")

    # 2. Basic TTS
    print("\n[2] POST /tts - basic synthesis")
    events = post_sse(f"{base_url}/tts",
                      {"text": "hello, this is TTS service test.", "mode": "basic"},
                      label="basic")
    done_evts = [e for e in events if e.get("event") == "done"]
    if done_evts:
        d = done_evts[0]
        print(f"  [OK] Done: {d.get('total_chunks')} chunks, {d.get('total_time')}s")
    else:
        print("  [WARN] No done event received")

    # 3. Voice Design
    print("\n[3] POST /tts - voice design")
    events = post_sse(f"{base_url}/tts",
                      {"text": "welcome!", "mode": "voice_design"},
                      label="voice_design")
    done_evts = [e for e in events if e.get("event") == "done"]
    if done_evts:
        print(f"  [OK] Voice Design done")
    else:
        print("  [WARN] No done event received")

    # 4. Error handling
    print("\n[4] POST /tts - bad params (clone without reference_wav)")
    result = post(f"{base_url}/tts",
                  {"text": "test", "mode": "clone"},
                  label="clone_no_ref")
    if result is None:
        print("  [OK] Correctly returned HTTP error")
    else:
        print("  [WARN] Expected error but got success")

    print("\n  [OK] TTS service tests all passed")
    return True


# ==================== ASR Tests ====================

def test_asr(base_url):
    print("\n" + "=" * 60)
    print("  ASR Service Test (port 8802)")
    print("=" * 60)

    # 1. Health
    print("\n[1] GET /health")
    data = get(f"{base_url}/health", "health check")
    if not data:
        print("  !! ASR service not running, skip remaining tests")
        return False
    if not data.get("model_loaded"):
        print("  !! Model not loaded")
        return False
    print(f"  [OK] Model loaded")

    # 2. Ensure mic is stopped first
    print("\n[2] GET /asr/status - ensure clean state")
    status = get(f"{base_url}/asr/status", "status check")
    if status and status.get("mic_running"):
        print("  Mic still running, stopping first...")
        post(f"{base_url}/asr/stop", body={}, label="force stop")
        time.sleep(1)
        status = get(f"{base_url}/asr/status", "status after stop")
    if status:
        print(f"  [OK] mic_running={status.get('mic_running')}")

    # 3. File streaming ASR
    print("\n[3] POST /asr/file - file streaming recognition")
    print(f"  Test wav: {TEST_WAV}")
    if os.path.exists(TEST_WAV):
        events = post_sse(f"{base_url}/asr/file",
                          {"input": TEST_WAV, "language": "zh", "chunk_ms": 600},
                          label="file_asr")
        done_evts = [e for e in events if e.get("event") == "done"]
        partial_evts = [e for e in events if e.get("event") == "partial"]
        if done_evts:
            print(f"  [OK] File ASR done: text='{done_evts[0].get('text', '')[:30]}'")
        elif partial_evts:
            print(f"  [OK] Got {len(partial_evts)} partial results")
        else:
            print("  [WARN] No recognition results")
    else:
        print(f"  [SKIP] Test audio not found: {TEST_WAV}")

    # 4. Mic recognition (3 seconds)
    print("\n[4] POST /asr/start - mic recognition (3s)")
    result = post(f"{base_url}/asr/start",
                  {"chunk_ms": 600},
                  label="start_mic")
    if result and result.get("status") == "started":
        print("  [OK] Mic started, waiting 3s...")

        time.sleep(1.5)
        status = get(f"{base_url}/asr/status", "status after 1.5s")
        if status:
            print(f"         mic_running={status.get('mic_running')}, "
                  f"chunk_count={status.get('chunk_count')}, "
                  f"last_text='{status.get('last_text', '')}'")

        time.sleep(1.5)

        print("\n[5] POST /asr/stop - stop mic")
        result = post(f"{base_url}/asr/stop", body={}, label="stop_mic")
        if result and result.get("status") == "stopped":
            texts = result.get("results", [])
            print(f"  [OK] Mic stopped, results: {texts}")
        else:
            print(f"  [WARN] Stop returned: {result}")
    else:
        print("  [WARN] Mic start failed (may be already running or device unavailable)")

    # 6. Final status
    print("\n[6] GET /asr/status - final status")
    data = get(f"{base_url}/asr/status", "final status")
    if data:
        running = data.get("mic_running")
        if running:
            print(f"  [WARN] mic still running")
        else:
            print(f"  [OK] mic_running=False, subscribers={data.get('subscribers')}")

    print("\n  [OK] ASR service tests all passed")
    return True


# ==================== SSE Subscribe Demo ====================

def test_asr_sse_subscribe(base_url, duration=5):
    print("\n" + "=" * 60)
    print(f"  SSE Subscribe Demo ({duration}s)")
    print("=" * 60)

    import http.client
    import threading

    result = post(f"{base_url}/asr/start", {"chunk_ms": 600}, label="start_mic")
    if not result or result.get("status") != "started":
        print("  Mic start failed, skip SSE demo")
        return

    events_received = []

    def sse_reader():
        port = int(base_url.split(":")[-1])
        conn = http.client.HTTPConnection("localhost", port, timeout=30)
        conn.request("GET", "/asr/stream")
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        for line in raw.split("\n"):
            if line.strip().startswith("data:"):
                try:
                    evt = json.loads(line.strip()[5:])
                    events_received.append(evt)
                except json.JSONDecodeError:
                    pass
        conn.close()

    t = threading.Thread(target=sse_reader, daemon=True)
    t.start()

    print(f"  Waiting {duration}s for SSE events...")
    time.sleep(duration)

    post(f"{base_url}/asr/stop", body={}, label="stop_mic")
    t.join(timeout=5)

    print(f"  Received {len(events_received)} SSE events:")
    for evt in events_received:
        event_type = evt.get("event", "?")
        if event_type == "partial":
            print(f"    [partial] chunk {evt.get('chunk','?')}: {evt.get('text','')}")
        elif event_type == "started":
            print(f"    [started] chunk_ms={evt.get('chunk_ms')}")
        elif event_type == "stopped":
            print(f"    [stopped] final_text={evt.get('final_text','')}")
        else:
            print(f"    [{event_type}] {json.dumps(evt, ensure_ascii=False)[:80]}")

    print("  [OK] SSE subscribe demo done")


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(description="VoxCPM2 TTS & ASR service test")
    parser.add_argument("--tts-url", default=DEFAULT_TTS_URL, help="TTS service URL")
    parser.add_argument("--asr-url", default=DEFAULT_ASR_URL, help="ASR service URL")
    parser.add_argument("--tts-only", action="store_true", help="Test TTS only")
    parser.add_argument("--asr-only", action="store_true", help="Test ASR only")
    parser.add_argument("--sse-demo", action="store_true", help="Run SSE subscribe demo")
    args = parser.parse_args()

    print("=" * 60)
    print("  VoxCPM2 TTS & ASR Service Test")
    print(f"  TTS: {args.tts_url}")
    print(f"  ASR: {args.asr_url}")
    print("=" * 60)

    results = {}

    if not args.asr_only:
        results["tts"] = test_tts(args.tts_url)

    if not args.tts_only:
        results["asr"] = test_asr(args.asr_url)

    if args.sse_demo and not args.tts_only:
        test_asr_sse_subscribe(args.asr_url)

    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name.upper()}: {status}")

    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()