@echo off
echo Starting VT Calendar Application...
echo.

echo Installing dependencies...
call npm install

echo.
echo Creating .env file from template...
if not exist .env (
    copy env.template .env
    echo .env file created. Please update with your API credentials.
) else (
    echo .env file already exists.
)

echo.
echo Starting server on http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

call npm start


