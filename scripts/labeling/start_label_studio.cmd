@echo off
setlocal
pushd "%~dp0..\.."

if not exist ".venv_labeling\Scripts\label-studio.exe" (
  echo Missing Label Studio. Run scripts\labeling\setup_labeling.cmd first.
  popd
  pause
  exit /b 1
)

".venv_labeling\Scripts\label-studio.exe" start
popd
pause
