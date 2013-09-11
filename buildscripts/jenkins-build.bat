REM
REM Copyright (C) 2011-13, DyND Developers
REM BSD 2-Clause License, see LICENSE.txt
REM
REM This is the master windows build + test script for building
REM pykit on jenkins.
REM
REM Jenkins Requirements:
REM   - Anaconda should be installed in C:\Anaconda.
REM   - Use a jenkins build matrix for multiple
REM     platforms/python versions
REM   - Use the XShell plugin to launch this script
REM   - Call the script from the root workspace
REM     directory as buildscripts/jenkins-build
REM   - Use a user-defined axis to select python versions with PYTHON_VERSION
REM

REM If no MSVC version is selected, choose 2010
if "%MSVC_VERSION%" == "" set MSVC_VERSION=10.0
REM Require a version of Python to be selected
if "%PYTHON_VERSION%" == "" exit /b 1

REM Jenkins has '/' in its workspace. Fix it to '\' to simplify the DOS commands.
set WORKSPACE=%WORKSPACE:/=\%

REM Remove the build subdirectory from last time
rd /q /s build

REM Use conda to create a conda environment of the required
REM python version and containing the dependencies.
SET PYENV_PREFIX=%WORKSPACE%\build\pyenv
C:\Anaconda\python .\buildscripts\create_conda_pyenv_retry.py %PYTHON_VERSION% %PYENV_PREFIX%
IF %ERRORLEVEL% NEQ 0 exit /b 1
echo on
set PYTHON_EXECUTABLE=%PYENV_PREFIX%\Python.exe
set PATH=%PYENV_PREFIX%;%PYENV_PREFIX%\Scripts;%PATH%

call C:\Anaconda\Scripts\conda install -p ${PYENV_PREFIX} llvmmath numpy

"%PYTHON_EXECUTABLE%" setup.py install
cd ..

REM Run the tests and generate xml results
%PYTHON_EXECUTABLE% -c "import pykit; pykit.test()"
IF %ERRORLEVEL% NEQ 0 exit /b 1

REM Get the version number and process it into a suitable form
FOR /F "delims=" %%i IN ('%PYTHON_EXECUTABLE% -c "import pykit; print(pykit.__version__)"') DO set VERSION=%%i
if "%VERSION%" == "" exit /b 1
set VERSION=%VERSION:-=_%

REM Put the conda package by itself in the directory pkgs/<anaconda-arch>
rd /q /s pkgs
mkdir pkgs
cd pkgs
mkdir win-%PYTHON_BITS%
cd win-%PYTHON_BITS%

REM Create a conda package from the build
call C:\Anaconda\Scripts\conda package -p %PYENV_PREFIX% --pkg-name=pykit --pkg-version=%VERSION%
IF %ERRORLEVEL% NEQ 0 exit /b 1
echo on

cd ..

exit /b 0
