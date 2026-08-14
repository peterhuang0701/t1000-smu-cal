@echo off
REM 在 Windows 上雙擊本檔案即可打包 SMU_Cal_Tool.exe
REM 需求: 已安裝 Python 3.9+ 並勾選 Add to PATH
cd /d %~dp0
echo === Installing dependencies ===
pip install --upgrade pyinstaller pyvisa pyvisa-py pyserial
if errorlevel 1 goto :err
echo === Building ===
pyinstaller --clean SMU_Cal_Tool.spec
if errorlevel 1 goto :err
echo.
echo === Done! exe 在 dist\SMU_Cal_Tool.exe ===
pause
exit /b 0
:err
echo.
echo *** Build FAILED, 檢查上面錯誤訊息 ***
pause
exit /b 1
