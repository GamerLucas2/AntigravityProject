@echo off
set PYTHONHTTPSVERIFY=0
echo [INFO] Instalando Pygbag para rodar o jogo no navegador...
python -m pip install pygbag --upgrade
echo [INFO] Iniciando servidor do jogo...
echo [INFO] Quando o servidor iniciar, acesse: http://localhost:8000
echo [INFO] Nao feche esta janela enquanto estiver jogando!
python run_web.py
pause
