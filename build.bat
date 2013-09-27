@ECHO OFF

python freeze.py py2exe
mkdir dist\data
xcopy data dist\data /E /Y
copy libtcod-mingw.dll dist
copy SDL.dll dist
copy terminal.png dist
copy license.txt dist
copy readme.md dist\readme.txt