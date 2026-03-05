@echo off
echo [INFO] Iniciando jogo local...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] O jogo fechou com erro ou o Python não está instalado.
    pause
)
