@echo off
chcp 65001 >nul
cd /d "C:\Users\Admin\Documents\陈嘉-资料备份\08.投资决策框架"
echo ================================================
echo   Weekly Data Update for Investment Framework
echo   %date% %time%
echo ================================================
echo.
C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe -X utf8 scripts\weekly_data_pull.py
echo.
echo Update complete. Check log at: logs/update_log.txt
pause