@echo off
set PYTHON_EXE=C:\Users\yusw1\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe

if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" -m PyInstaller --noconsole --onefile --name bory src/cli.py
) else (
  python -m PyInstaller --noconsole --onefile --name bory src/cli.py
)

if errorlevel 1 (
  echo.
  echo Build failed. Check the message above.
  pause
)
