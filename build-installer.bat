@echo off
rem The .hapkg files are the installers for this repository, so this runs the same build.
call "%~dp0build.bat"
exit /b %errorlevel%
