"""
Hughson-Westlake Algoritması
"""

from __future__ import annotations
from functools import reduce
from typing import Optional
from models import (
    Response, FrequencyTestState, AudiogramState,
    Ear, START_DB, TEST_ORDER, MIN_DB, MAX_DB
)


# ─────────────────────────────────────────────
# SABİTLER
# ─────────────────────────────────────────────

HEARING_LEVELS: tuple[str, ...] = (
    "Normal İşitme",
    "Hafif işitme kaybı",
    "Orta derece işitme kaybı",
    "Orta-ileri derece işitme kaybı",
    "İleri derece işitme kaybı",
    "Çok ileri derece işitme kaybı",
)


# ─────────────────────────────────────────────
# Sonraki dB seviyesini belirle
# ─────────────────────────────────────────────

def next_level(current_db: int, heard: bool) -> int:
    """
    BME kuralı:
      - Duyulduysa → 10 dB azalt
      - Duyulmadıysa → 5 dB artır

    SAF FONKSİYON: Aynı girdi her zaman aynı çıktıyı verir.
    """
    return current_db - 10 if heard else current_db + 5


# ─────────────────────────────────────────────
# İşitme kaybı sınıflandırması
# ─────────────────────────────────────────────

def classify_hearing(threshold_db: int) -> str:
    match threshold_db:
        case db if db<=25:
            return "Normal İşitme"
        case db if db <= 40:
            return "Hafif işitme kaybı"
        case db if db <= 55:
            return "Orta derece işitme kaybı"
        case db if db <= 70:
            return "Orta-ileri derece işitme kaybı"
        case db if db <= 90:
            return "İleri derece işitme kaybı"
        case _:
            return "Çok ileri derece işitme kaybı"


# ─────────────────────────────────────────────
# Yanıt analizi
# ─────────────────────────────────────────────

def get_heard_levels(responses: tuple[Response, ...], frequency: int) -> list[int]:
    """
    Belirli bir frekansta DUYULAN seviyeleri döndürür.
    filter → duyulan yanıtları seç
    map    → sadece dB değerlerini al
    """
    return list(map(
        lambda r: r.level_db,
        filter(lambda r: r.frequency == frequency and r.heard, responses)
    ))


def get_unheard_levels(responses: tuple[Response, ...], frequency: int) -> list[int]:
    """
    Belirli bir frekansta DUYULMAYAN seviyeleri döndürür.
    filter → duyulmayan yanıtları seç
    map    → sadece dB değerlerini al
    """
    return list(map(
        lambda r: r.level_db,
        filter(lambda r: r.frequency == frequency and not r.heard, responses)
    ))


def summarize_responses(responses: tuple[Response, ...], frequency: int) -> dict:
    """
    Bir frekansa ait tüm yanıtların özetini döndürür.
    reduce → toplam duyulan / duyulmayan sayısını hesaplar.
    """
    initial = {"heard_count": 0, "unheard_count": 0}

    freq_responses = list(filter(lambda r: r.frequency == frequency, responses))

    return reduce(
        lambda acc, r: {
            "heard_count": acc["heard_count"] + (1 if r.heard else 0),
            "unheard_count": acc["unheard_count"] + (0 if r.heard else 1)
        },
        freq_responses,
        initial
    )


# ─────────────────────────────────────────────
# Eşik belirleme
# ─────────────────────────────────────────────

def determine_threshold(responses: tuple[Response, ...], frequency: int) -> Optional[int]:
    """
    BME kuralı: Yukarı çıkıldıktan (5 dB artış) sonra
    duyulan ilk seviye eşik olarak kabul edilir.

    Yani: bir "duymadı" sonrası gelen "duydu" → eşik.
    """
    heard_levels = get_heard_levels(responses, frequency)
    unheard_levels = get_unheard_levels(responses, frequency)

    # Henüz hem duyulan hem duyulmayan yoksa eşik belirlenemez
    if not heard_levels or not unheard_levels:
        return None

    last = responses[-1]

    # Son yanıt "duydu" ise ve daha önce duyulmayan bir seviye varsa → eşik
    if last.heard and last.frequency == frequency:
        return last.level_db

    return None


# ─────────────────────────────────────────────
# ANA FONKSİYON: Yanıt işle, state güncelle
# ─────────────────────────────────────────────

def process_response(state: FrequencyTestState, heard: bool) -> FrequencyTestState:
    """
    Yeni bir RESPONSE geldiğinde:
      1. Yanıtı state'e ekler
      2. Eşik belirlendiyse state'i tamamlar
      3. Belirlenemediyse sonraki dB seviyesini hesaplar

    SAF FONKSİYON — orijinal state değişmez, yeni state döner.
    """
    # Yanıtı kaydet
    response = Response(
        frequency=state.frequency,
        level_db=state.current_db,
        heard=heard,
        ear=state.ear
    )
    new_state = state.add_response(response)

    # Eşik belirlendi mi?
    threshold = determine_threshold(new_state.responses, state.frequency)
    if threshold is not None:
        return new_state.set_threshold(threshold)

    # Eşik belirlenemediyse sonraki seviyeyi hesapla
    # MIN_DB ve MAX_DB sınırları aşılmamalı
    next_db = max(MIN_DB, min(MAX_DB, next_level(state.current_db, heard)))
    return new_state.set_current_db(next_db)


# ─────────────────────────────────────────────
# COM EKİBİNE BAĞLANTI NOKTASI
# ─────────────────────────────────────────────

def handle_response_message(state: FrequencyTestState, heard: bool) -> tuple[FrequencyTestState, dict]:
    """
    COM ekibinin socket sunucusu bu fonksiyonu çağırır.
    heard → Java'dan gelen RESPONSE mesajı var mı? (True/False)

    Döndürür:
      - güncellenmiş state (bir sonraki yanıtta kullanılacak)
      - Java'ya gönderilecek JSON dict
    """
    new_state = process_response(state, heard)

    result = {
        "frequency": state.frequency,
        "next_db": new_state.current_db,
        "is_complete": new_state.is_complete,
        "threshold": new_state.threshold,
        "classification": classify_hearing(new_state.threshold) if new_state.threshold else None
    }
    return new_state, result


