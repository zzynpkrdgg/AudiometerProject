"""
Python Socket Sunucusu — Java GUI ile Entegrasyon

Java GUI'den JSON formatında mesajlar alır:
  {"frekans": "1000", "db": 40, "kulak": "right"}

Hughson-Westlake algoritmasını çalıştırır
ve sonucu geri gönderir.
"""

import socket
import json
import sys
from threading import Thread

from models import AudiogramState, Ear, Response
from HughsonWestlake import handle_response_message, process_response

# ─────────────────────────────────────────────
# DURUM YÖNETİMİ
# ─────────────────────────────────────────────

# Her kulak için ayrı odyogram
audiograms = {
    "right": AudiogramState.initial(ear=Ear.RIGHT),
    "left": AudiogramState.initial(ear=Ear.LEFT)
}

# Her frekans/kulak kombinasyonu için state
frequency_states = {}


# ─────────────────────────────────────────────
# MESAJ AYRIŞTIRICISI VE İŞLEYİCİSİ
# ─────────────────────────────────────────────

def handle_client(conn, addr):
    """
    Java istemcisinden gelen mesajları işler.
    """
    print(f"[BAĞLANDI] {addr}")
    
    try:
        while True:
            # Java'dan JSON mesajı al
            data = conn.recv(1024).decode('utf-8').strip()
            
            if not data:
                break
            
            print(f"[ALINDI] {data}")
            
            try:
                # JSON'u ayrıştır
                message = json.loads(data)
                frequency = int(message.get("frekans"))
                db = int(message.get("db"))
                ear = message.get("kulak", "right")
                
                # Yanıt gelip gelmediği belirleniyor (test mesajı olarak değerlendir)
                # Gerçek uygulamada serial porttan RESPONSE geldikten sonra True olur
                # Burada demo amaçlı True kabul edelim
                heard = True
                
                # Algoritma çalıştır
                state_key = f"{frequency}_{ear}"
                
                if state_key not in frequency_states:
                    # İlk kez bu frekans test ediliyor
                    ear_enum = Ear.RIGHT if ear == "right" else Ear.LEFT
                    from models import FrequencyTestState, START_DB
                    frequency_states[state_key] = FrequencyTestState(
                        frequency=frequency,
                        ear=ear_enum,
                        current_db=START_DB
                    )
                
                current_state = frequency_states[state_key]
                new_state, result = handle_response_message(current_state, heard)
                frequency_states[state_key] = new_state
                
                # Sonucu JSON olarak hazırla ve Java'ya gönder
                response = {
                    "status": "ok",
                    "frequency": result["frequency"],
                    "next_db": result["next_db"],
                    "is_complete": result["is_complete"],
                    "threshold": result["threshold"],
                    "classification": result["classification"]
                }
                
                response_json = json.dumps(response, ensure_ascii=False)
                conn.sendall((response_json + "\n").encode('utf-8'))
                
                print(f"[GÖNDERİLDİ] {response_json}")
                
            except Exception as e:
                # Hata durumunda Java'ya hata mesajı gönder
                error_response = {
                    "status": "error",
                    "message": str(e)
                }
                error_json = json.dumps(error_response, ensure_ascii=False)
                conn.sendall((error_json + "\n").encode('utf-8'))
                print(f"[HATA] {e}")
    
    except Exception as e:
        print(f"[BAĞLANTI HATASI] {addr}: {e}")
    
    finally:
        conn.close()
        print(f"[KAPATILDI] {addr}")


# ─────────────────────────────────────────────
# SOCKET SUNUCUSU
# ─────────────────────────────────────────────

def start_server(host="localhost", port=5050):
    """
    Port 5050'de dinleyen socket sunucusunu başlatır.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"🎵 Python Sunucusu başladı!")
    print(f"   Adres: {host}:{port}")
    print(f"   Java GUI'den bağlantıları bekliyorum...\n")
    
    try:
        while True:
            conn, addr = server_socket.accept()
            # Her istemci için ayrı thread başlat
            client_thread = Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
    
    except KeyboardInterrupt:
        print("\n\n[KAPATILIYOR] Sunucu durduruldu.")
    
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
