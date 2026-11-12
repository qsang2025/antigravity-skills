@echo off
setlocal
title KET NOI GEMINI 4 VOI ANTIGRAVITY

:: Chuyen den dung thu muc chua file .bat
cd /d "%~dp0"

echo ==============================================================================
echo   DANG KHOI TAO HE THONG KET NOI GEMINI 4 ARGON VOI ANTIGRAVITY...
echo ==============================================================================
echo.

:: Kiem tra Python tren may nguoi dung
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
    goto RUN_INSTALL
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py
    goto RUN_INSTALL
)

echo [LOI] Khong tim thay Python tren may tinh cua ban!
echo [!] Vui long tai va cai dat Python tu: https://www.python.org/downloads/
echo [!] Luu y nho tich chon: "Add Python to PATH" khi cai dat.
echo.
pause
exit /b 1

:RUN_INSTALL
echo Dang su dung trinh thuc thi: %PY_CMD%
echo.
%PY_CMD% install_gemini_antigravity.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Qua trinh cai dat gap loi hoac can kiem tra lai.
    echo.
) else (
    echo.
    echo [HOAN TAT] He thong da san sang! Ban co the dong cua so nay va su dung Antigravity.
    echo.
)

pause
