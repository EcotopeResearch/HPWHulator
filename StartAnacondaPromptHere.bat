@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
REM echo Searching for conda...
REM set root=C:\Users\%USERNAME%\AppData\Local\Continuum\anaconda3\condabin
REM if exist %root%\ (
REM 	call %root%\Scripts\activate.bat %root%
REM ) else (
REM  	echo Could not find anaconda on the root path, you can set it manually in the batch. 
REM  	pause
REM )

REM The %~dp0 (that’s a zero) variable when referenced within a Windows batch file will expand to the drive letter and path of that batch file.
cd /d %~dp0 //

echo Looking for the environment file...
for /r "." %%a in (*) do (
	IF "%%~xa"==".yml" (
		IF %%~pa == %~p0 (
			set p=%%~na
		)
	)
)

IF defined p (
	echo Found enivronment file: %p%.yml
	echo Setting up the environment from file...
	call conda env update --file %p%.yml
	for /f "tokens=1,2 delims= " %%G in (%p%.yml) do (
		IF "%%G"=="name:" (
			set q=%%H
		)
	)
	echo Activating the enivronment found in %p%.yml, !q!...
) else ( 
	echo ERROR: No conda environment file found in this directory, looking for a .yml file.
	pause
)
call conda activate %q%
REM Needed to keep the thing open as anaconda terminal
%windir%\system32\cmd.exe
