@echo off
title Odyometre Sistemi Entegre Baslatici
echo ==========================================
echo   ODYOMETRE SISTEMI BASLATILIYOR...
echo ==========================================

:: 1. PYTHON SUNUCUSUNU (SERVER.PY) AYRI BIR PENCEREDE BASLAT
echo [1/2] Python Algoritma Sunucusu aciliyor...
:: Kanka burayı server.py olarak güncelledik, asıl sunucu bu!
start "Python Algoritma Sunucusu" cmd /k python server.py

:: Python sunucusunun tamamen hazır olması için 3 saniye bekle
timeout /t 3 /nobreak > nul

:: 2. JAVA KODLARINI DERLE VE CALISTIR
echo [2/2] Java Arayuzu derleniyor ve baslatiliyor...
javac -cp ".;jSerialComm-2.11.4.jar" *.java

if %errorlevel% neq 0 (
    echo.
    echo HATA: Java derlenirken bir sorun olustu! 
    echo Lutfen sistemde JDK yuklu oldugundan emin olun.
    pause
    exit /b
)

:: Java uygulamasını ana sınıf (Main) üzerinden çalıştır
java -cp ".;jSerialComm-2.11.4.jar" Main

echo.
echo Sistem kapatildi.
pause