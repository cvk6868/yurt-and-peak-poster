# Draaien op je eigen Windows-computer

De computer moet op het geplande tijdstip aan staan en online zijn. Staat hij uit, dan wordt de post de volgende keer dat hij aangaat alsnog gemaakt (de taak start "zodra mogelijk").

## Eenmalig installeren
1. Pak de zip uit, bijvoorbeeld naar `C:\yurt-and-peak`.
2. Open PowerShell (Windows-toets, typ "PowerShell", Enter) en voer uit, één voor één:
   - `winget install Python.Python.3.12`
   - `winget install Gyan.FFmpeg`
3. Sluit PowerShell en open hem opnieuw. Voer uit: `pip install pillow requests`
4. Controleer met `python --version` en `ffmpeg -version`.
5. Kopieer `geheim-voorbeeld.bat` naar `geheim.bat` en open die in Kladblok. Vul je sleutels in (Anthropic en Cloudinary). Sla op.

## Proefrun (plaatst niets)
Dubbelklik op `start.bat`, of voer uit: `start.bat droog pauze`. Kijk daarna in de map `uit` voor de slides of de video en de caption, en in `log.txt` voor meldingen.

## Dagelijks automatisch laten draaien
Pas als de proefrun goed is en je Instagram-sleutels (`IG_USER_ID`, `IG_TOKEN`) in `geheim.bat` staan: dubbelklik op `plan-taak.bat`. Dit maakt de taak `YurtAndPeak-post` aan, elke dag om 19:00. Stoppen kan via Taakplanner: rechtermuisknop op de taak, Verwijderen.
