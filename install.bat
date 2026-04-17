@echo off
chcp 1251 >nul
cd /d "%~dp0"

echo ==========================================
echo  Установка 1C MCP Server
echo ==========================================

:: 1. Python
echo [1/4] Ищем Python...
python --version >nul 2>&1
if %errorlevel% neq 0 goto CHECK_PY
set PYTHON_CMD=python
goto PYTHON_OK

:CHECK_PY
py --version >nul 2>&1
if %errorlevel% neq 0 goto NO_PY
set PYTHON_CMD=py

:PYTHON_OK
%PYTHON_CMD% --version
echo OK.
goto VENV_CHECK

:NO_PY
echo ОШИБКА: Python не найден. Установите его с python.org
pause & exit /b

:: 2. Venv
:VENV_CHECK
echo [2/4] Проверяем venv...
if exist "venv" goto VENV_OK
echo Создаем venv (подождите)...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 goto VENV_ERR
echo OK.
goto REQ_INSTALL

:VENV_ERR
echo ОШИБКА создания venv!
pause & exit /b

:VENV_OK
echo venv уже есть.
goto REQ_INSTALL

:: 3. Requirements
:REQ_INSTALL
echo [3/4] Устанавливаем библиотеки...
call venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 goto PIP_ERR
echo OK.
goto PROJ_INSTALL

:PIP_ERR
echo ОШИБКА pip install!
pause & exit /b

:: 4. Project
:PROJ_INSTALL
echo [4/4] Устанавливаем проект...
call venv\Scripts\pip.exe install -e .
if %errorlevel% neq 0 goto PROJ_ERR
echo OK.
goto DONE

:PROJ_ERR
echo ОШИБКА установки проекта!
pause & exit /b

:: Finish
:DONE
echo ==========================================
echo Готово! Всё установлено.
echo ==========================================
pause