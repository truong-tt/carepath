@echo off
setlocal
pushd "%~dp0..\.."

echo [1/3] Creating Python environment: .venv_labeling
py -3.12 -m venv .venv_labeling
if errorlevel 1 goto error

echo [2/3] Upgrading pip
".venv_labeling\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error

echo [3/3] Installing Whisper and Label Studio
".venv_labeling\Scripts\python.exe" -m pip install -r requirements-labeling.txt
if errorlevel 1 goto error

echo.
echo Done. You can close this window.
popd
pause
exit /b 0

:error
echo.
echo Setup failed. Copy the error text and ask for help.
popd
pause
exit /b 1
