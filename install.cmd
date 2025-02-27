@echo off

:: Get the current directory where the CMD file is executing
set "currentDir=%~dp0"

:: Define the path to the virtual environment
set "venvPath=%currentDir%venv"

:: Check if the virtual environment exists
if not exist "%venvPath%" (
    echo Virtual environment not found. Creating it...
    python -m venv "%venvPath%"
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Exiting.
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists. Skipping creation.
)

set "dot_envPath=%currentDir%.env"
:: Check if the .env file exists
if exist "%dot_envPath%" (
    echo .ENV file already exists at %dot_envPath%. Skipping creation.
) else (
    echo .ENV file not found. Creating a copy of it from Sample.env. Please make sure to open .evn and put in your own API keys and Azure OpenAI deployment paths
    copy "%currentDir%Sample.env" "%dot_envPath%"
)

@echo Activating Environment
call %venvPath%\scripts\activate

@echo Upgrading pip installer to latest
python.exe -m pip install --upgrade pip

@echo Installing required packages
pip install -r requirements.txt --require-virtualenv


@echo Installation Complete - After your .env is updated with apikey and deployment paths, run the following command to start the application
pause