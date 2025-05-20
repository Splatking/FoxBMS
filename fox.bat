@SETLOCAL EnableExtensions EnableDelayedExpansion

@PUSHD "%~dp0"

@SET "ENV_NAME=2024-08-pale-fox"

@SET "FOXBMS_PYTHON_ENV_DIRECTORY_USER=%USERPROFILE%\foxbms-envs\%ENV_NAME%"
@SET "FOXBMS_PYTHON_ENV_DIRECTORY_ROOT=C:\foxbms-envs\%ENV_NAME%"

@SET "FOXBMS_PYTHON_ENV_DIRECTORY=%FOXBMS_PYTHON_ENV_DIRECTORY_USER%"

@REM Prefer the user installation

@IF NOT EXIST "%FOXBMS_PYTHON_ENV_DIRECTORY_USER%" (
    @SET "FOXBMS_PYTHON_ENV_DIRECTORY=%FOXBMS_PYTHON_ENV_DIRECTORY_ROOT%"
)

@IF NOT EXIST "%FOXBMS_PYTHON_ENV_DIRECTORY%" (
    @ECHO "%FOXBMS_PYTHON_ENV_DIRECTORY_USER%" and
    @ECHO "%FOXBMS_PYTHON_ENV_DIRECTORY_ROOT%" do not exist.
    @ECHO One of both must be available. See Installation instructions in
    @ECHO "%~dp0\INSTALL.md"
    @EXIT /b 1
)

@CALL "%FOXBMS_PYTHON_ENV_DIRECTORY%\Scripts\activate.bat"

@REM If the activation script failed, exit with error
@IF %ERRORLEVEL% NEQ 0 (
    @ECHO The activation script of the environment is missing.
    @EXIT /b %ERRORLEVEL%
)

@REM Check if Python executable exists
@SET PYTHON_EXE=python
@WHERE "%PYTHON_EXE%" 1>NUL 2>NUL
@IF %ERRORLEVEL% NEQ 0 (
    @EXIT /b %ERRORLEVEL%
)

@REM The environment is setup, so let's run the application
@"%PYTHON_EXE%" "%~dp0\fox.py" %*

@REM if fox.py failed, exit with this error
@IF %ERRORLEVEL% NEQ 0 (
    @EXIT /b %ERRORLEVEL%
)
@POPD
