@echo off
setlocal
cd /d "%~dp0"
title Gerar Verificador de vetor - Cromotransfer
echo ================================================
echo   VERIFICADOR DE VETOR - CROMOTRANSFER
echo   Criando aplicativo desktop e atalho
echo ================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado. Instale Python 3.11 ou mais recente e tente novamente.
  goto error
)
echo [1/4] Instalando dependencias...
python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo [2/4] Instalando PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 goto error
echo.
echo [3/4] Gerando aplicativo em pasta otimizada. Pode demorar alguns minutos...
python -m PyInstaller --noconfirm --clean --onedir --windowed --name "Verificador_de_vetor_Cromotransfer" --icon "assets\logo_icone.ico" --collect-all PySide6 --collect-all pymupdf --add-data "assets;assets" app_desktop.py
if errorlevel 1 goto error
if not exist "dist\Verificador_de_vetor_Cromotransfer\Verificador_de_vetor_Cromotransfer.exe" goto error
echo.
echo [4/4] Criando atalho na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$exe = Join-Path (Get-Location) 'dist\Verificador_de_vetor_Cromotransfer\Verificador_de_vetor_Cromotransfer.exe'; $desk = [Environment]::GetFolderPath('Desktop'); $ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut((Join-Path $desk 'Verificador de vetor - Cromotransfer.lnk')); $sc.TargetPath = $exe; $sc.WorkingDirectory = Split-Path $exe; $sc.Save()"
if errorlevel 1 (
  echo Nao foi possivel criar o atalho automaticamente.
  echo O EXE esta na pasta dist. Crie um atalho manualmente.
  goto done
)
echo.
echo CONCLUIDO! O atalho foi criado na Area de Trabalho.
echo Para distribuir a outros computadores, copie toda a pasta dist\Verificador_de_vetor_Cromotransfer.
echo O Windows pode solicitar validacao de seguranca. Nao desative as protecoes.
goto done
:error
echo.
echo Ocorreu um erro. Confira as mensagens acima.
:done
echo.
pause
