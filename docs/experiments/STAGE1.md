# Stage 1 — Application Sandbox and IPC

Goal: test Android application-level data isolation and exported ContentProvider boundaries on Android 13 (API 33) and Android 16 (API 36). Two apps are used; both target SDK 33.

| ID | Test | Expected |
|---|---|---|
| S1 | SecurityOwner creates and reads its private file | ALLOW |
| S2 | SecurityClient reads the same private path directly | DENY |
| S3 | SecurityClient queries a non-exported provider | DENY |
| S4 | SecurityClient queries an exported provider | ALLOW |
| S5 | SecurityClient queries a provider protected by signature-level permission without requesting it | DENY |

Evidence: `report.json`, `lab-logcat.txt`, `owner.png`, `client.png`. The host reads the owner's private test file using `run-as` only to verify fixture presence; this host operation is NOT used as evidence that the client can read the file. The file contains no sensitive information.

A `null` result from ContentResolver is treated as INCONCLUSIVE rather than an access-control denial. If the positive control (S4) or fixture fails, negative observations are not considered valid. Tests run from regular Android application UIDs without root. A passing result demonstrates the documented boundary in this selected emulator configuration only, not physical hardware assurance.

The GitHub Actions workflow writes a separate `README.md` section bracketed by `ANDROID_STAGE1_START/END`. It does not edit the infrastructure-readiness section.
