"""
Testler
Birim testleri  : pytest ile, somut senaryolar
Property testleri: hypothesis ile, genel kurallar

Çalıştırmak için:
    pip install pytest hypothesis
    pytest test_audiometer.py -v
"""

import pytest
from hypothesis import given, assume
from hypothesis import strategies as st

from models import (
    Response, FrequencyTestState, AudiogramState,
    Ear, START_DB, TEST_ORDER, TEST_FREQUENCIES, MIN_DB, MAX_DB
)
from HughsonWestlake import (
    next_level, classify_hearing, HEARING_LEVELS,
    get_heard_levels, get_unheard_levels, summarize_responses,
    determine_threshold, process_response
)


# ─────────────────────────────────────────────
# YARDIMCI — test verisi üreten saf fonksiyonlar
# ─────────────────────────────────────────────

def make_response(frequency: int, level_db: int, heard: bool, ear: Ear = Ear.RIGHT) -> Response:
    return Response(frequency=frequency, level_db=level_db, heard=heard, ear=ear)

def make_state(frequency: int = 1000, ear: Ear = Ear.RIGHT) -> FrequencyTestState:
    return FrequencyTestState(frequency=frequency, ear=ear)


# ═════════════════════════════════════════════
# BİRİM TESTLERİ
# ═════════════════════════════════════════════

class TestNextLevel:
    """Yeni BME kuralı: test seviyesi her adımda 5 artar (30-80 aralığında)"""

    def test_increases_by_5(self):
        assert next_level(40) == 45

    def test_increases_from_min_db(self):
        assert next_level(30) == 35

    def test_increases_approaching_max(self):
        assert next_level(75) == 80


class TestClassifyHearing:
    """30-80 dB aralığında sınıflandırma tablosu"""

    def test_mild_loss_lower_bound(self):
        assert classify_hearing(30) == "Hafif işitme kaybı"

    def test_mild_loss(self):
        assert classify_hearing(40) == "Hafif işitme kaybı"

    def test_moderate_loss_lower_bound(self):
        assert classify_hearing(41) == "Orta derece işitme kaybı"

    def test_moderate_loss(self):
        assert classify_hearing(55) == "Orta derece işitme kaybı"

    def test_moderate_severe_loss_lower_bound(self):
        assert classify_hearing(56) == "Orta-ileri derece işitme kaybı"

    def test_moderate_severe_loss(self):
        assert classify_hearing(70) == "Orta-ileri derece işitme kaybı"

    def test_severe_loss_lower_bound(self):
        assert classify_hearing(71) == "İleri derece işitme kaybı"

    def test_severe_loss(self):
        assert classify_hearing(80) == "İleri derece işitme kaybı"


class TestFilterMap:
    """map / filter fonksiyonlarının doğruluğu"""

    def setup_method(self):
        """Her testten önce sabit bir yanıt listesi hazırla"""
        self.responses = (
            make_response(1000, 40, True),
            make_response(1000, 45, True),
            make_response(1000, 50, False),
            make_response(1000, 55, True),
            make_response(500,  40, True),   # farklı frekans
        )

    def test_get_heard_levels_filters_correct_frequency(self):
        result = get_heard_levels(self.responses, 1000)
        assert 40 in result
        assert 45 in result
        assert 55 in result

    def test_get_heard_levels_excludes_other_frequency(self):
        result = get_heard_levels(self.responses, 1000)
        # 500 Hz'deki 40 dB bu listeye girmemeli
        assert len(result) == 3

    def test_get_unheard_levels(self):
        result = get_unheard_levels(self.responses, 1000)
        assert result == [50]

    def test_get_heard_levels_empty_when_none_heard(self):
        responses = (make_response(1000, 40, False),)
        assert get_heard_levels(responses, 1000) == []


class TestSummarizeResponses:
    """reduce ile yanıt özeti"""

    def test_counts_correctly(self):
        responses = (
            make_response(1000, 40, True),
            make_response(1000, 45, False),
            make_response(1000, 50, True),
        )
        summary = summarize_responses(responses, 1000)
        assert summary["heard_count"] == 2
        assert summary["unheard_count"] == 1

    def test_empty_responses(self):
        summary = summarize_responses((), 1000)
        assert summary["heard_count"] == 0
        assert summary["unheard_count"] == 0

    def test_excludes_other_frequencies(self):
        responses = (
            make_response(1000, 40, True),
            make_response(500,  40, True),  # farklı frekans
        )
        summary = summarize_responses(responses, 1000)
        assert summary["heard_count"] == 1


class TestDetermineThreshold:
    """BME kuralı: duymadı sonrası duydu → eşik"""

    def test_threshold_after_unheard(self):
        responses = (
            make_response(1000, 30, False),
            make_response(1000, 35, True),   # duymadı sonrası duydu → eşik
        )
        assert determine_threshold(responses, 1000) == 35

    def test_no_threshold_without_unheard(self):
        # Hiç duymadı yoksa eşik belirlenemez
        responses = (
            make_response(1000, 30, True),
            make_response(1000, 35, True),
        )
        assert determine_threshold(responses, 1000) is None

    def test_no_threshold_without_heard(self):
        responses = (
            make_response(1000, 30, False),
            make_response(1000, 35, False),
        )
        assert determine_threshold(responses, 1000) is None

    def test_no_threshold_if_last_is_unheard(self):
        # Son yanıt duymadı ise eşik belirlenmez
        responses = (
            make_response(1000, 30, True),
            make_response(1000, 35, False),
        )
        assert determine_threshold(responses, 1000) is None


class TestProcessResponse:
    """process_response saf fonksiyon davranışı"""

    def test_immutability(self):
        """Orijinal state değişmemeli"""
        state = make_state()
        new_state = process_response(state, True)
        assert state.responses == ()       # orijinal değişmedi
        assert len(new_state.responses) == 1

    def test_response_increases_current_db_by_5(self):
        """Duyulsa da duyulmasa da 5 dB artmalı (yeni kural)"""
        state = make_state()
        state = state.set_current_db(30)
        
        # Duydu
        new_state_heard = process_response(state, True)
        assert new_state_heard.current_db == 35 
        
        # Duymadı
        new_state_unheard = process_response(state, False)
        assert new_state_unheard.current_db == 35

    def test_completes_after_threshold(self):
        """duymadı → duydu → tamamlanmalı"""
        state = make_state()
        state = state.set_current_db(30)
        state = process_response(state, False)  # duymadı
        state = process_response(state, True)   # duydu → eşik
        assert state.is_complete is True
        assert state.threshold is not None


class TestAudiogramState:
    """AudiogramState — test sırası ve tamamlanma"""

    def test_initial_creates_all_frequencies(self):
        audiogram = AudiogramState.initial(Ear.RIGHT)
        for freq in TEST_ORDER:
            assert audiogram.get_state(freq) is not None

    def test_next_frequency_follows_test_order(self):
        """TEST_ORDER sırasına göre ilk frekansı döndürmeli"""
        audiogram = AudiogramState.initial(Ear.RIGHT)
        assert audiogram.next_frequency() == TEST_ORDER[0]  # 1000 Hz vb.

    def test_next_frequency_skips_completed(self):
        audiogram = AudiogramState.initial(Ear.RIGHT)
        state_first = audiogram.get_state(TEST_ORDER[0]).set_threshold(30)
        audiogram = audiogram.update_state(state_first)
        assert audiogram.next_frequency() == TEST_ORDER[1] 

    def test_next_frequency_none_when_all_complete(self):
        audiogram = AudiogramState.initial(Ear.RIGHT)
        for freq in TEST_ORDER:
            completed = audiogram.get_state(freq).set_threshold(35)
            audiogram = audiogram.update_state(completed)
        assert audiogram.next_frequency() is None

    def test_is_complete_only_when_all_done(self):
        audiogram = AudiogramState.initial(Ear.RIGHT)
        assert audiogram.is_complete() is False

    def test_right_and_left_ear_independent(self):
        """Sağ ve sol kulak birbirini etkilememeli"""
        right = AudiogramState.initial(Ear.RIGHT)
        left  = AudiogramState.initial(Ear.LEFT)
        right_updated = right.update_state(right.get_state(1000).set_threshold(35))
        assert left.get_state(1000).threshold is None  # sol etkilenmedi


# ═════════════════════════════════════════════
# PROPERTY-BASED TESTLERİ
# Her zaman geçerli olan genel kurallar
# ═════════════════════════════════════════════

class TestNextLevelProperties:

    @given(st.integers(MIN_DB, MAX_DB - 5))
    def test_always_increases_by_5(self, db):
        """Herhangi bir dB'de sonuç her zaman 5 fazla olmalı"""
        assert next_level(db) == db + 5

    @given(st.integers(MIN_DB, MAX_DB - 5))
    def test_result_always_greater_than_input(self, db):
        """Yeni değer her zaman eskiden büyük olmalı"""
        assert next_level(db) > db


class TestClassifyHearingProperties:

    @given(st.integers(30, 40))
    def test_mild_loss_range(self, db):
        assert classify_hearing(db) == "Hafif işitme kaybı"

    @given(st.integers(41, 55))
    def test_moderate_loss_range(self, db):
        assert classify_hearing(db) == "Orta derece işitme kaybı"

    @given(st.integers(56, 70))
    def test_moderate_severe_loss_range(self, db):
        assert classify_hearing(db) == "Orta-ileri derece işitme kaybı"

    @given(st.integers(71, 80))
    def test_severe_loss_range(self, db):
        assert classify_hearing(db) == "İleri derece işitme kaybı"

    @given(st.integers(MIN_DB, MAX_DB))
    def test_always_returns_string(self, db):
        """Herhangi bir dB için her zaman string dönmeli"""
        result = classify_hearing(db)
        assert isinstance(result, str)
        assert len(result) > 0


class TestImmutabilityProperties:

    @given(st.booleans())
    def test_process_response_never_mutates_original(self, heard):
        """
        Herhangi bir heard değeri için
        orijinal state her zaman değişmez kalmalı
        """
        state = make_state()
        original_responses = state.responses
        original_db = state.current_db
        process_response(state, heard)           # çağır ama sonucu kullanma
        assert state.responses == original_responses  # değişmedi
        assert state.current_db == original_db        # değişmedi


class TestFilterMapProperties:

    @given(st.lists(st.booleans(), min_size=0, max_size=11))
    def test_heard_plus_unheard_equals_total(self, heard_list):
        """
        Duyulan + duyulmayan sayısı toplam yanıt sayısına eşit olmalı
        """
        responses = tuple(
            make_response(1000, 30 + (i * 5), h) for i, h in enumerate(heard_list)
        )
        heard   = get_heard_levels(responses, 1000)
        unheard = get_unheard_levels(responses, 1000)
        assert len(heard) + len(unheard) == len(heard_list)

    @given(st.lists(st.booleans(), min_size=0, max_size=11))
    def test_summarize_matches_filter(self, heard_list):
        """
        summarize_responses (reduce) sonucu
        filter ile sayılanla aynı olmalı
        """
        responses = tuple(
            make_response(1000, 30 + (i * 5), h) for i, h in enumerate(heard_list)
        )
        summary = summarize_responses(responses, 1000)
        assert summary["heard_count"]   == len(get_heard_levels(responses, 1000))
        assert summary["unheard_count"] == len(get_unheard_levels(responses, 1000))