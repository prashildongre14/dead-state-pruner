@echo off
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Dead-State Pruner.lnk');$s.TargetPath='%~dp0START_HERE.bat';$s.WorkingDirectory='%~dp0';$s.IconLocation='%~dp0icon.ico';$s.WindowStyle=7;$s.Description='Dead-State Pruner';$s.Save()"
echo.
echo Done! Look for "Dead-State Pruner" on your Desktop.
pause
