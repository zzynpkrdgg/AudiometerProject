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
    # Bu frekansa ait tüm yanıtları al
    freq_responses = list(filter(lambda r: r.frequency == frequency, responses))
    
    # Eşik belirlemek için minimum 2 yanıt gerekli
    if len(freq_responses) < 2:
        return None
    
    # Son iki yanıtı kontrol et
    prev = freq_responses[-2]
    last = freq_responses[-1]
    
    # BME kuralı: "duymadı" sonrası "duydu" → eşik bulundu
    if not prev.heard and last.heard:
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

def handle_response_message(audiogram: AudiogramState, heard: bool) -> tuple[AudiogramState, dict]:
    """
    COM ekibinin socket sunucusu bu fonksiyonu çağırır.
    heard → Java'dan gelen RESPONSE mesajı var mı? (True/False)

    Mevcut frekansı belirler, yanıtı işler, ve frekans tamamlandığında
    otomatik olarak sıradaki frekansa geçer.

    Döndürür:
      - güncellenmiş AudiogramState (tüm frekansların durumu)
      - Java'ya gönderilecek JSON dict (mevcut veya sıradaki frekans bilgileri)

    SAF FONKSİYON — orijinal AudiogramState değişmez, yeni bir kopya döner.
    """
    # TEST_ORDER sırasına göre tamamlanmamış ilk frekansı bul
    current_frequency = audiogram.next_frequency()
    if current_frequency is None:
        # Tüm frekanslar tamamlandı
        return audiogram, {"error": "All frequencies completed"}
    
    # Mevcut frekansın test durumunu al
    current_state = audiogram.get_state(current_frequency)
    
    # Yanıtı işle (eşik belirleme veya sonraki dB seviyesi hesaplama)
    new_state = process_response(current_state, heard)
    
    # AudiogramState'i güncellenmiş state ile update et
    updated_audiogram = audiogram.update_state(new_state)
    
    # Eğer bu frekans için eşik belirlendiyse sıradaki frekansa geç
    if new_state.is_complete:
        next_freq = updated_audiogram.next_frequency()
        
        if next_freq is not None:
            # Sıradaki frekans var, onun state'ini hazırla
            next_state = updated_audiogram.get_state(next_freq)
            result = {
                "frequency": next_freq,
                "next_db": next_state.current_db,
                "is_complete": False,
                "threshold": None,
                "classification": None,
                "previous_frequency": current_frequency,
                "previous_threshold": new_state.threshold,
                "previous_classification": classify_hearing(new_state.threshold)
            }
        else:
            # Tüm frekanslar tamamlandı
            result = {
                "frequency": None,
                "next_db": None,
                "is_complete": True,
                "threshold": None,
                "classification": None,
                "all_completed": True,
                "thresholds": updated_audiogram.get_thresholds()
            }
    else:
        # Bu frekans henüz tamamlanmadı, aynı frekansla devam et
        result = {
            "frequency": current_frequency,
            "next_db": new_state.current_db,
            "is_complete": False,
            "threshold": None,
            "classification": None
        }
    
    return updated_audiogram, result


