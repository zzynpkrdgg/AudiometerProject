"""
Odyometre Projesi - Veri Modelleri
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Optional
from enum import Enum
import socket
import json


TEST_FREQUENCIES: tuple[int, ...] = (250, 500, 1000, 2000, 4000, 8000)

"""dB aralığı"""
MIN_DB: int = -10
MAX_DB: int = 120

"""kulak"""
class Ear(Enum):
    RIGHT="right"
    LEFT="left"

#TEMEL MODEL->Tek bir hasta yanıtı
@dataclass(frozen=True)
class TestResponse:
    frequency:int
    level_db:int
    heard:bool
    ear:Ear
    
    def __post_init__(self)->None:
        if self.frequency not in TEST_FREQUENCIES:
            raise ValueError(f"Geçersiz frekans: {self.frequency}."
                             f"Geçerli frekans değerleri: {TEST_FREQUENCIES}")
                            
        if not (MIN_DB<=self.level_db<=MAX_DB):
            raise ValueError(f"Geçersiz db seviyesi:{self.level_db}."
                             f"Geçerli db seviye aralığı:{MIN_DB}-{MAX_DB}")

#MODEL: Bir frekans için tüm test durumu
@dataclass(frozen=True)
class FrequencyTestState:
    """
    responses -> o frekansa ait tüm yanıtlar
    threshold -> eşik değeri belirlendiyse db değeri, belirlenmediyse None
    is_complete -> test tamamlandı mı?
    """
    
    frequency:int
    ear:Ear
    responses:tuple[TestResponse,...]=()
    threshold:Optional[int]=None
    is_complete:bool=False

    def add_response(self,response:TestResponse)->FrequencyTestState:
        """
        yeni bir yanıt ekler ve yeni bir state döndürür
        """
        new_responses=self.responses + (response,)
        return replace(self,responses=new_responses)
    
    def set_threshold(self,threshold_db:int)->FrequencyTestState:
        return replace(self,threshold=threshold_db,is_complete=True)
    
#MODEL -> Tüm testin durumu(tüm frekanslar)
@dataclass(frozen=True)
class AudiogramState:
    ear:Ear
    states:tuple[FrequencyTestState,...]

    @staticmethod
    def initial(ear:Ear)->AudiogramState:
        """
        Factory fonksiyonudur (yan etkisiz).
        Tüm frekanslar için boş başlangıç durumu oluşturur.
        """
        initial_states=tuple(
            FrequencyTestState(frequency=freq,ear=ear)
            for freq in TEST_FREQUENCIES        
        )
        return AudiogramState(ear=ear,states=initial_states)
    def get_state(self,frequancy:int)->FrequencyTestState:
        """
        Belirtilen frekansın durumunu döndürür.
        """
        return next(
            (s for s in self.states if s.frequency==frequancy),
            None
        )
    def update_state(self,updated:FrequencyTestState)->AudiogramState:
        """
        Belirtilen fonksiyonun güncellenmiş değerini döndürür.
        Yeni bir AudiogramState döndürür - orijinal değişmez.
        """
        new_states=tuple(
            updated if s.frequency ==updated.frequency else s
            for s in self.states
        )
        return replace(self, states=new_states)

    def is_complete(self)->bool:
        """
        Tüm frekanslar için eşik değerler belirlendiğini kontrol eder.
        """     
        return all(s.is_complete for s in self.states)
    def get_thresholds(self)->dict[int,Optional[int]]:
        """
        Frekans ve eşik dB eşlemesini döndürür.
        Odyogram çizmek için kullanılır.
        """
        return {s.frequency:s.threshold for s in self.states}
    
#DEMO-> Çalıştırılabilir örnek
if __name__=="__main__":
    #sağ kulak için boş odyogram oluşturalım
    audiogram=AudiogramState.initial(ear=Ear.RIGHT)
    print("başlangıç durumu")
    print(audiogram.get_thresholds())

    #1000 Hz'de bir yanıt ekleyelim
    response=TestResponse(frequency=1000,level_db=40,heard=True,ear=Ear.RIGHT)
    state_1000=audiogram.get_state(1000)
    updated_state=state_1000.add_response(response)

    #eşiği belirleyelim ve kaydedelim
    final_state=updated_state.set_threshold(40)
    audiogram=audiogram.update_state(final_state)

    print("1000 Hz eşiği belirlendikten sonra")
    print(audiogram.get_thresholds())
    # → {250: None, 500: None, 1000: 40, 2000: None, 4000: None, 8000: None}
    
    print("orijinal state değişti mi?")
    print("state_1000:",state_1000.threshold)
    print("updated_state:",final_state.threshold)
    

# Bu fonksiyon yazılım ekibinin yazdığı algoritmaya bağlanacak
def hughson_westlake_isle(frekans, db, kulak):
    # BURASI YAZILIM EKİBİNİN KENDİ FONKSİYONLARINI ÇAĞIRACAĞI YER
    # Örnek bir dönüş hazırladım:
    return {"status": "success", "sonraki_adim": "10 dB azalt", "yeni_db": db - 10}

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5050))
    server.listen(1)
    print("Python Algoritması 5050 portunda Java'yı bekliyor...")

    while True:
        try:
            conn, addr = server.accept()
            data = conn.recv(1024).decode('utf-8')
            if data:
                # Java'dan gelen veriyi JSON olarak oku
                istek = json.loads(data)
                print(f"Java'dan gelen veri: {istek}")
                
                # Algoritmayı çalıştır
                cevap = hughson_westlake_isle(istek['frekans'], istek['db'], istek['kulak'])
                
                # Java'ya cevabı geri gönder
                conn.send(json.dumps(cevap).encode('utf-8'))
            conn.close()
        except Exception as e:
            print("Hata:", e)

if __name__ == "__main__":
    start_server()
       