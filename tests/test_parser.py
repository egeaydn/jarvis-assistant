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

def test_parser_cases() -> None:
    """Türkçe komut örneklerinin doğru action ve argümanlara dönüştüğünü doğrular."""
    for raw, exp_action, exp_target, exp_query in cases:
        result = parse(raw)

        assert result["action"] == exp_action, raw
        assert result["target"] == exp_target, raw
        if exp_query is not None:
            assert result.get("query") == exp_query, raw

