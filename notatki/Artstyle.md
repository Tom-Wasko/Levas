[[Główny obraz]] · [[Zarys aplikacji]]

# Artstyle

Styl mapy jest kreskówkowy, przypominający grę Good Pizza, Great Pizza. Tak samo wnętrza lokali i postacie.

## Interpretacja do zrobienia bez grafika
Wszystko jest rysowane w kodzie jako **SVG** (grafika wektorowa). Claude może takie rysunki wygenerować i poprawiać bez pomocy grafika, pliki są małe, a obraz ostry na każdym ekranie.

### Zasady
- **Płaskie kolory i gruby kontur.** Każdy kształt ma kontur 2–3 px w ciemnym kolorze (ciemny brąz albo granat, nie czarny) i jedno wypełnienie. Najwyżej jeden cień: ciemniejszy odcień tego samego koloru po stronie odwróconej od światła.
- **Proste bryły.** Budynki to prostopadłościany, dachy to trójkąty i trapezy, okna to prostokąty. Wszystkie rogi są lekko zaokrąglone (4–8 px) – stąd miękki, kreskówkowy wygląd.
- **Rzut izometryczny 2.5D.** Mapa to siatka kafli 2:1 (np. 128 × 64 px). Budynek zajmuje 1, 2 albo 4 kafle. Wszystkie budynki są w tej samej skali i stoją w równych rzędach – czytelność jest ważniejsza niż realizm.
- **Ograniczona paleta.** 12–16 kolorów zapisanych jako zmienne CSS (np. `--trawa`, `--ulica`, `--cegla`, `--dach`, `--szklo`), osobno dla motywu jasnego i ciemnego. Kolory ciepłe i nasycone, ale nie jaskrawe.
- **Marki rozpoznawalne po kolorach.** Budynek sklepu jest w barwach marki (np. Biedronka czerwono-żółta, IKEA niebiesko-żółta), a szyld ma nazwę zwykłą czcionką – bez kopiowania logotypów. Okna marek naśladują kolory i układ ich stron, nie ich grafiki.
- **Postacie z prostych figur.** Głowa to koło, tułów to zaokrąglony prostokąt, oczy to dwie kropki. Postacie różnią się fryzurą, kolorem ubrania i jednym dodatkiem (czapka, okulary, fartuch). Są składane losowo z części, więc każdy pracownik i klient wygląda inaczej.
- **Unikatowe lokale.** Wnętrze kebabu jest składane z wymiennych elementów: lada, rożen, tablica menu, kafelki, lampy, rośliny, kolor ścian. Zestaw zależy od wyborów drużyny i ziarna gry, więc żadne dwa lokale nie wyglądają tak samo.
- **Oszczędny ruch.** Tylko proste animacje CSS: kołyszący się szyld, para nad rożnem, przechodnie idący chodnikiem.
- **Jedna czcionka.** Zaokrąglona, bezszeryfowa, z polskimi znakami (np. Nunito albo Baloo 2 z Google Fonts).
