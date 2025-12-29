@echo off
set PYTHON_EXE=C:\Users\yusw1\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe

if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" -m src.cli
) else (
  python -m src.cli
)

if errorlevel 1 (
  echo.
  echo Program exited with an error. Check the message above.
  pause
)
