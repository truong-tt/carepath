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
  echo Created data\labeling\audio
  echo Copy your audio files into that folder, then run this file again.
  popd
  pause
  exit /b 1
)

echo Running Whisper. First run may be slow because the model must download.
".venv_labeling\Scripts\python.exe" scripts\labeling\transcribe_for_label_studio.py ^
  --audio-dir data\labeling\audio ^
  --output data\labeling\label_studio_tasks.json %*
if errorlevel 1 goto error

echo.
echo Done. Import this file into Label Studio:
echo C:\Users\ADMIN\carepath\data\labeling\label_studio_tasks.json
popd
pause
exit /b 0

:error
echo.
echo Transcription failed. Copy the error text and ask for help.
popd
pause
exit /b 1
