# Dagelijks automatisch posten: instellen in stappen

Reken op een avond. Alleen jij kunt inloggen op je eigen accounts.

## 1. GitHub
1. Maak een gratis account op github.com en maak een nieuwe **private** repository (bijvoorbeeld `yurt-and-peak-posts`).
2. Pak de zip uit en sleep alle bestanden en mappen, inclusief de verborgen map `.github`, naar de repository (Add file > Upload files). Controleer dat `.github/workflows/dagelijks.yml` erbij staat.

## 2. Sleutels als geheimen
In de repository: Settings > Secrets and variables > Actions > New repository secret. Maak deze zes:

| Naam | Waar haal je het vandaan |
| --- | --- |
| ANTHROPIC_API_KEY | console.anthropic.com > API keys |
| CLOUDINARY_CLOUD, CLOUDINARY_KEY, CLOUDINARY_SECRET | Gratis account op cloudinary.com; staan op je dashboard. Hier komt elke post tijdelijk online te staan, want Instagram haalt de media van een openbaar webadres. |
| IG_USER_ID, IG_TOKEN | Zie stap 3 |

Voeg **IG_USER_ID en IG_TOKEN pas toe nadat de test uit stap 4 goed is gegaan.** Zonder die twee kan de taak niets plaatsen: hij maakt dan alleen de post en stopt met een foutmelding.

## 3. Instagram koppelen (het lastigste deel)
1. Zet het Instagram-account op Business of Creator en koppel het aan een Facebook-pagina.
2. Maak op developers.facebook.com een app (type Business). Voeg het product Instagram toe, met **Facebook Login** (niet Instagram Login: alleen daarmee werkt de muziekfunctie).
3. Vraag in Graph API Explorer een token met de rechten `instagram_basic`, `instagram_content_publish`, `pages_show_list` en `pages_read_engagement`.
4. Maak er een langlopend token van en haal daarmee het **paginatoken** op (`/me/accounts`). Een paginatoken dat uit een langlopend gebruikerstoken komt, verloopt niet. Dat is je `IG_TOKEN`.
5. Je `IG_USER_ID` haal je op met `/{pagina-id}?fields=instagram_business_account`.
Zolang de app in ontwikkelmodus staat en jij beheerder bent, kun je hem voor je eigen account gebruiken zonder Meta-goedkeuring.

## 4. Testen
1. Vul `feiten.md` aan (zie hieronder) en commit.
2. Ga naar Actions > Dagelijkse Instagram-post > Run workflow, met "droog" op `true`.
3. Open na afloop de download `laatste-post`. Daarin staan de slides of de Reel, `caption.txt` en `controle.txt`.
4. Ziet het er goed uit? Voeg IG_USER_ID en IG_TOKEN toe en draai nogmaals met "droog" op `false`.

Daarna plaatst de taak elke dag om 18:00 UTC (19:00 in de winter, 20:00 in de zomer), afwisselend een carrousel en een Reel.

## Feiten
De AI gebruikt alleen wat in `feiten.md` staat. Zijn de feiten op, dan stopt de taak met de melding "vul feiten.md aan" en plaatst hij niets. GitHub mailt je dan. Voeg regelmatig gecontroleerde feiten over Kirgizië en Oezbekistan toe, elk met bron en datum.

## Muziek
- Reels krijgen bij het plaatsen muziek van Instagram (`audio_zoekterm` in `instellingen.json`, nu "acoustic"). Je kunt vooraf niet horen welk nummer het wordt, en Instagram bepaalt welke muziek beschikbaar is.
- Carrousels krijgen geen muziek via de API.
- Liever vaste muziek? Zet in `instellingen.json` `"muziek": "eigen"` en zet royaltyvrije tracks in de map `muziek/`.
