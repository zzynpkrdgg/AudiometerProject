"""
Veri Modelleri
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Optional
from enum import Enum


# ─────────────────────────────────────────────
# SABİTLER
# ─────────────────────────────────────────────

# test frekansları
TEST_FREQUENCIES: tuple[int, ...] = (250, 500, 1000, 2000, 4000, 8000)

# test sırası
# 1000 Hz günlük konuşmayı algılama için önemli olduğundan önce test edilir
TEST_ORDER: tuple[int, ...] = (1000, 2000, 4000, 8000, 500, 250)

# BME dokümanına göre başlangıç dB seviyesi
# 26-40 aralığı hafif işitme kaybı olduğundan 40 dB'den başlanır
START_DB: int = 40

# dB aralığı
MIN_DB: int = -10
MAX_DB: int = 120


# ─────────────────────────────────────────────
# ENUM: Kulak tarafı
# ─────────────────────────────────────────────

class Ear(Enum):
    """Hangi kulağın test edildiğini belirtir."""
    RIGHT = "right"   # Odyogramda kırmızı O
    LEFT  = "left"    # Odyogramda mavi X


# ─────────────────────────────────────────────
# TEMEL MODEL: Tek bir hasta yanıtı
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class Response:
    """
    Hastanın tek bir sese verdiği yanıtı temsil eder.
    RESPONSE mesajı geldiyse heard=True, gelmezse heard=False.
    """
    frequency: int   # Hz cinsinden frekans
    level_db: int    # Desibel cinsinden ses seviyesi
    heard: bool      # Hasta sesi duydu mu?
    ear: Ear         # Hangi kulak test edildi?

    def __post_init__(self) -> None:
        if self.frequency not in TEST_FREQUENCIES:
            raise ValueError(f"Geçersiz frekans: {self.frequency}. "
                             f"Geçerli değerler: {TEST_FREQUENCIES}")
        if not (MIN_DB <= self.level_db <= MAX_DB):
            raise ValueError(f"Geçersiz dB seviyesi: {self.level_db}. "
                             f"Aralık: {MIN_DB}–{MAX_DB}")


# ─────────────────────────────────────────────
# MODEL: Bir frekans için tüm test durumu
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class FrequencyTestState:
    """
    Belirli bir frekans ve kulak için testin anlık durumu.

    responses   → o frekansa ait tüm yanıtlar (immutable tuple)
    threshold   → eşik belirlendiyse dB değeri, henüz belirlenemediyse None
    is_complete → test tamamlandı mı?
    current_db  → şu an test edilen dB seviyesi (START_DB ile başlar)
    """
    frequency: int
    ear: Ear
    responses: tuple[Response, ...] = ()
    threshold: Optional[int] = None
    is_complete: bool = False
    current_db: int = START_DB

    def add_response(self, response: Response) -> FrequencyTestState:
        """
        Yeni bir yanıt ekler ve yeni bir state döndürür.
        Orijinal nesne DEĞİŞMEZ.
        """
        new_responses = self.responses + (response,)
        return replace(self, responses=new_responses)

    def set_threshold(self, threshold_db: int) -> FrequencyTestState:
        """Eşiği kaydeder ve testi tamamlandı olarak işaretler."""
        return replace(self, threshold=threshold_db, is_complete=True)

    def set_current_db(self, db: int) -> FrequencyTestState:
        """Sonraki dB seviyesini günceller. Yeni bir state döndürür."""
        return replace(self, current_db=db)


# ─────────────────────────────────────────────
# MODEL: Tüm testin durumu (tüm frekanslar)
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class AudiogramState:
    """
    Odyometri testinin tamamını temsil eder.
    Sağ ve sol kulak ayrı ayrı test edilir.
    Her frekans için FrequencyTestState tutulur.
    """
    ear: Ear
    states: tuple[FrequencyTestState, ...]

    @staticmethod
    def initial(ear: Ear) -> AudiogramState:
        """
        Tüm frekanslar için boş başlangıç durumu oluşturur.
        TEST_ORDER sırasına göre oluşturulur.
        """
        initial_states = tuple(
            FrequencyTestState(frequency=freq, ear=ear)
            for freq in TEST_ORDER
        )
        return AudiogramState(ear=ear, states=initial_states)

    def get_state(self, frequency: int) -> Optional[FrequencyTestState]:
        """Belirtilen frekansın durumunu döndürür."""
        return next(
            (s for s in self.states if s.frequency == frequency),
            None
        )

    def update_state(self, updated: FrequencyTestState) -> AudiogramState:
        """
        Belirtilen frekansın durumunu günceller.
        Yeni bir AudiogramState döndürür — orijinal değişmez.
        """
        new_states = tuple(
            updated if s.frequency == updated.frequency else s
            for s in self.states
        )
        return replace(self, states=new_states)

    def is_complete(self) -> bool:
        """Tüm frekanslar için eşik belirlendi mi?"""
        return all(s.is_complete for s in self.states)

    def next_frequency(self) -> Optional[int]:
        """
        TEST_ORDER sırasına göre henüz tamamlanmamış
        ilk frekansı döndürür.
        Tüm frekanslar tamamlandıysa None döner.
        """
        return next(
            (freq for freq in TEST_ORDER
             if not self.get_state(freq).is_complete),
            None
        )

    def get_thresholds(self) -> dict[int, Optional[int]]:
        """
        Frekans → eşik dB eşlemesini döndürür.
        Odyogram çizmek için kullanılır.
        Sağ kulak için O, sol kulak için X sembolü COM ekibi tarafından çizilir.
        """
        return {s.frequency: s.threshold for s in self.states}


