@echo off
echo [INFO] Instalando Pygbag para rodar o jogo no navegador...
pip install pygbag --upgrade
echo [INFO] Iniciando servidor do jogo...
echo [INFO] Quando o servidor iniciar, acesse: http://localhost:8000
echo [INFO] Nao feche esta janela enquanto estiver jogando!
pygbag .
pause
