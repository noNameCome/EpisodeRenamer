@echo off
echo Converting icon.png to icon.ico...
python -c "from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(256,256),(64,64),(32,32),(16,16)])"

echo Cleaning previous build...
if exist RenaMatcher.spec del RenaMatcher.spec
if exist build rmdir /s /q build

echo Building RenaMatcher...
pyinstaller --onefile --windowed --icon icon.ico --add-data "icon.ico;." --collect-all tkinterdnd2 --name RenaMatcher main.py

echo.
echo Build complete! Check dist folder.
pause
