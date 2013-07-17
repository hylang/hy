@ECHO OFF

REM Make batch file for Hy development

if "%1" == "" goto help

if "%1" == "help" (
    :help
    echo. No default step. Use setup.py
    echo.
    echo.  Other targets:
    echo.
    echo.    - docs
    echo.    - full
    echo.
    echo.    - dev "test & flake"
    echo.    - flake
    echo.    - test
    echo.    - diff
    echo.    - tox
    echo.    - d
    echo.    - r
    echo.
    goto end
)

if "%1" == "docs" (
:docs
    echo.docs not yet supported under Windows
goto :EOF
)

if "%1" == "upload" (
:upload
    python setup.py sdist upload
goto :EOF
)

if "%1" == "clear" (
:clear
    cls
goto :EOF
)

if "%1" == "d" (
:d
    call :clear
    call :dev
goto :EOF
)

if "%1" == "test" (
:test
    call :venv
    nosetests -sv
goto :EOF
)

if "%1" == "venv" (
:venv
    echo.%VIRTUAL_ENV% | findstr /C:"hy" 1>nul
    if errorlevel 1 (
        echo.You're not in a Hy virtualenv. FOR SHAME
    ) ELSE (
        echo.We're properly in a virtualenv. Going ahead.
    )
goto :EOF
)

if "%1" == "flake" (
:flake
    echo.flake8 hy
    flake8 hy
goto :EOF
)

if "%1" == "dev" (
:dev
    call :test
    call :flake
goto :EOF
)

if "%1" == "tox" (
:tox
    call :venv
    tox -e "py26,py27,py32,py33,flake8"
goto :EOF
)

if "%1" == "d" (
:d
    call :clear
    call :dev
goto :EOF
)

if "%i" == "diff" (
:diff
    git diff --color
goto :EOF
)

if "%1" == "r" (
:r
    call :d
    call :tox
    call :diff
goto :EOF
)

if "%1" == full (
    call :docs
    call :d
    call :tox
)