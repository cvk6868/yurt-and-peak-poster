@echo off
cd /d "%~dp0"
echo Maakt een dagelijkse taak aan die elke dag om 19:00 echt een post plaatst.
echo Gebruik dit pas als de proefrun goed is en de Instagram-sleutels in geheim.bat staan.
pause
powershell -NoProfile -Command "$a = New-ScheduledTaskAction -Execute '%~dp0start.bat' -Argument 'echt' -WorkingDirectory '%~dp0'; $t = New-ScheduledTaskTrigger -Daily -At 19:00; $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun; Register-ScheduledTask -TaskName 'YurtAndPeak-post' -Action $a -Trigger $t -Settings $s -Force"
echo Klaar. Controleer in Taakplanner (Task Scheduler) of YurtAndPeak-post bestaat.
pause
