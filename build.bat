@ECHO OFF

python freeze.py py2exe
mkdir dist\data
mkdir dist\data\maps
xcopy data\items dist\data\items /i /E /Y
xcopy data\life dist\data\life /i /E /Y
xcopy data\text dist\data\text /i /E /Y
xcopy data\tiles dist\data\tiles /i /E /Y
copy libtcod-mingw.dll dist
copy SDL.dll dist
copy terminal.png dist
copy license.txt dist
copy readme.md dist\readme.txt
git log --pretty=format:"%%h" -n 1 > dist\git-version.txt