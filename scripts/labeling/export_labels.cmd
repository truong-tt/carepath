@echo off
setlocal
pushd "%~dp0..\.."

if not exist ".venv_labeling\Scripts\python.exe" (
  echo Missing .venv_labeling. Run scripts\labeling\setup_labeling.cmd first.
  popd
  pause
  exit /b 1
)

if not exist "data\labeling\label_studio_export.json" (
  echo Missing export file:
  echo C:\Users\ADMIN\carepath\data\labeling\label_studio_export.json
  echo Export JSON from Label Studio and save it with that exact name.
  popd
  pause
  exit /b 1
)

".venv_labeling\Scripts\python.exe" scripts\labeling\export_label_studio_transcripts.py ^
  --input data\labeling\label_studio_export.json ^
  --output data\labeling\training_transcripts.jsonl
if errorlevel 1 goto error

echo.
echo Done. Training file:
echo C:\Users\ADMIN\carepath\data\labeling\training_transcripts.jsonl
popd
pause
exit /b 0

:error
echo.
echo Export conversion failed. Copy the error text and ask for help.
popd
pause
exit /b 1
