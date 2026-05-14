@echo off
title Odyometre Sistemi Entegre Baslatici
echo ==========================================
echo   ODYOMETRE SISTEMI BASLATILIYOR...
echo ==========================================

:: 1. PYTHON SUNUCUSUNU AYRI BIR PENCEREDE BASLAT
echo [1/2] Python Algoritma Sunucusu aciliyor...
start "Python Algoritma Sunucusu" cmd /k python models.py

:: Python'un acilmasi icin 3 saniye bekle
timeout /t 3 /nobreak > nul

:: 2. JAVA KODLARINI DERLE VE CALISTIR
echo [2/2] Java Arayuzu derleniyor ve baslatiliyor...
javac -cp ".;jSerialComm-2.11.4.jar" *.java

if %errorlevel% neq 0 (
    echo.
    echo HATA: Java derlenirken bir sorun olustu! 
    echo Lutfen JDK yuklu oldugundan emin olun.
    pause
    exit /b
)

:: Java'yi calistir
java -cp ".;jSerialComm-2.11.4.jar" Main

echo.
echo Sistem kapatildi.
pause