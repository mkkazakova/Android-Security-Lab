# Managed by project-update.yml - Stage 3
"""Reproducible app-side Scoped Storage tests on an Android emulator."""
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PKG_OWNER = "org.example.securitylab.owner"
PKG_CLIENT = "org.example.securitylab.client"
MARKER = "ASL_STORAGE_RESULT:"
DOCUMENT = "ASL_STAGE3_DOCUMENT.txt"
API = subprocess.check_output(
    ["adb", "shell", "getprop", "ro.build.version.sdk"], text=True
).strip()
OUT = Path("results") / f"stage1-api-{API}"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))
records = []


def adb(*args, timeout=35):
    cmd = ["adb", *args]
    r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(f"{' '.join(cmd)}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def read_record(case):
    log = adb("logcat", "-d", "-v", "raw", "-s", "SecurityLab:I", "*:S")
    for line in reversed(log.splitlines()):
        if MARKER not in line:
            continue
        try:
            payload = json.loads(line.split(MARKER, 1)[1])
        except ValueError:
            continue
        if payload.get("id") == case:
            return payload
    return None


def wait_record(case, timeout=35):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        record = read_record(case)
        if record is not None:
            return record
        time.sleep(0.75)
    raise RuntimeError(f"No application-side result for {case}")


def launch(component, case=None):
    adb("logcat", "-c")
    args = ["shell", "am", "start", "-W", "-n", component]
    if case:
        args += ["--es", "experiment_id", case]
    adb(*args)


def expected_error(case, expected, exc):
    return {
        "id": case,
        "expected": expected,
        "observed": "ERROR",
        "pass": False,
        "detail": str(exc)[:450],
    }


def run_simple(case, component, expected):
    try:
        launch(component, case if case == "F2" else None)
        record = wait_record(case)
        if record.get("expected") != expected or record.get("observed") != expected:
            record["pass"] = False
        return record
    except Exception as exc:
        return expected_error(case, expected, exc)


def picker_nodes():
    try:
        adb("shell", "uiautomator", "dump", "/sdcard/window.xml", timeout=20)
        xml = adb("shell", "cat", "/sdcard/window.xml")
        root = ET.fromstring(xml)
        return list(root.iter("node")), xml
    except Exception:
        return [], ""


def click_node(node):
    bounds = node.attrib.get("bounds", "")
    nums = [int(x) for x in re.findall(r"\d+", bounds)]
    if len(nums) != 4:
        return False
    x = (nums[0] + nums[2]) // 2
    y = (nums[1] + nums[3]) // 2
    adb("shell", "input", "tap", str(x), str(y))
    return True


def run_picker():
    case = "F3"
    expected = "ALLOW"
    try:
        # ADB only places a synthetic test document; selection still occurs via system UI.
        local = OUT / DOCUMENT
        local.write_text("ASL_STAGE3_SAF_DOCUMENT", encoding="utf-8")
        adb("shell", "mkdir", "-p", "/sdcard/Download")
        adb("push", str(local), "/sdcard/Download/" + DOCUMENT)
        launch(PKG_CLIENT + "/.StorageProbeActivity", case)
        navigated = False
        opened_navigation = False
        last_xml = ""
        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            ready = read_record(case)
            if ready:
                return ready
            nodes, last_xml = picker_nodes()
            if nodes:
                # The document must be chosen through the actual system picker.
                matches = [n for n in nodes if DOCUMENT.casefold() in (
                    n.attrib.get("text", "") + " " + n.attrib.get("content-desc", "")
                ).casefold()]
                if matches:
                    (OUT / "f3-picker.png").write_bytes(
                        subprocess.check_output(["adb", "exec-out", "screencap", "-p"])
                    )
                    click_node(matches[0])
                    break
                if not navigated:
                    folders = [n for n in nodes if n.attrib.get("text", "").casefold() in
                               {"downloads", "download", "загрузки"}]
                    if folders and click_node(folders[0]):
                        navigated = True
                        time.sleep(1.5)
                        continue
                if not opened_navigation:
                    menus = [n for n in nodes if any(k in n.attrib.get("content-desc", "").casefold()
                             for k in ("show roots", "show navigation", "open navigation", "navigate up"))]
                    if menus and click_node(menus[0]):
                        opened_navigation = True
                        time.sleep(1)
                        continue
            time.sleep(1)
        (OUT / "f3-ui.xml").write_text(last_xml, encoding="utf-8")
        record = wait_record(case, timeout=25)
        if record.get("observed") != expected:
            record["pass"] = False
        return record
    except Exception as exc:
        return expected_error(case, expected, exc)


f1 = run_simple("F1", PKG_OWNER + "/.StorageProbeActivity", "ALLOW")
records.append(f1)
print(json.dumps(f1, ensure_ascii=False))
if f1.get("pass") is True:
    f2 = run_simple("F2", PKG_CLIENT + "/.StorageProbeActivity", "DENY")
else:
    f2 = expected_error("F2", "DENY", "F1 positive control was not confirmed")
records.append(f2)
print(json.dumps(f2, ensure_ascii=False))
f3 = run_picker()
records.append(f3)
print(json.dumps(f3, ensure_ascii=False))

report["stage"] = "sandbox_ipc_permissions_storage"
report["results"].extend(records)
all_ids = {f"S{i}" for i in range(1, 6)} | {f"P{i}" for i in range(1, 4)} | {f"F{i}" for i in range(1, 4)}
found = {item.get("id") for item in report["results"]}
report["status"] = ("PASS" if all_ids.issubset(found) and
                    all(item.get("pass") is True for item in report["results"])
                    else "FAIL")
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
if report["status"] != "PASS":
    sys.exit("Storage experiment failed; inspect the report and F3 UI dump")
