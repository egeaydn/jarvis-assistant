# -*- coding: utf-8 -*-
"""Parser smoke tests — Phase 2 + Phase 3"""
from app.brain.command_parser import parse

cases = [
    # Phase 2 — mevcut
    ("chrome aç",                      "open",        "chrome",              None),
    ("chrome'u aç",                     "open",        "chrome",              None),
    ("discord'u kapat",                 "close",       "discord",             None),
    ("spotify aç",                      "open",        "spotify",             None),
    ("açık uygulamaları göster",        "list_apps",   None,                  None),
    ("çalışan uygulamalar",             "list_apps",   None,                  None),
    ("sistem bilgisi",                  "system_info", None,                  None),
    ("sistem bilgilerini göster",       "system_info", None,                  None),
    ("çıkış",                           "exit",        None,                  None),
    ("exit",                            "exit",        None,                  None),
    ("merhaba",                         "unknown",     None,                  None),
    # Phase 3 — yeni
    ("youtube aç",                      "open_web",    "https://youtube.com", None),
    ("github'ı aç",                     "open_web",    "https://github.com",  None),
    ("python ara",                      "search_web",  None,                  "python"),
    ("web'de django öğren",             "search_web",  None,                  "django öğren"),
    ("readme.md dosyasını bul",         "find_file",   "readme.md",           "readme.md"),
]

passed = 0
failed = 0
for raw, exp_action, exp_target, exp_query in cases:
    r = parse(raw)
    ok = (
        r["action"] == exp_action
        and r["target"] == exp_target
        and (exp_query is None or r.get("query") == exp_query)
    )
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"[{status}] {raw!r}")
        print(f"       beklenen  action={exp_action!r} target={exp_target!r} query={exp_query!r}")
        print(f"       gelen     action={r['action']!r} target={r['target']!r} query={r.get('query')!r}")
        continue
    print(f"[{status}] {raw!r:45s}  action={r['action']!r:14s}  target={r['target']!r}")

print(f"\n{passed}/{passed+failed} test geçti.")

