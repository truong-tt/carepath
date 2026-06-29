@echo off
setlocal
pushd "%~dp0..\.."

if not exist ".venv_labeling\Scripts\python.exe" (
  echo Missing .venv_labeling. Run scripts\labeling\setup_labeling.cmd first.
  popd
  pause
  exit /b 1
)

if not exist "data\labeling\audio" (
  mkdir "data\labeling\audio"
)

".venv_labeling\Scripts\python.exe" scripts\labeling\serve_audio.py --dir data\labeling\audio --port 8765
popd
pause
