# Logowanie kontem Microsoft (szkolnym) – krok po kroku

Bez tej konfiguracji Levas działa normalnie: uczniowie logują się loginem i hasłem, które zakłada mistrz gry
(zakładka *Drużyny*). Logowanie kontem Microsoft dodaje na stronie logowania przycisk **Zaloguj kontem
Microsoft** – uczeń wpisuje swój szkolny adres (np. `jan.kowalski@szkola.edu.pl`) i hasło od Teams/Office.
Hasła wpisuje się na stronie Microsoftu, Levas ich nigdy nie widzi.

Potrzebne są trzy rzeczy od Microsoftu: **identyfikator aplikacji (client ID)**, **identyfikator dzierżawy
(tenant ID)** szkoły i **klucz tajny (client secret)**. Zdobywa się je raz, rejestrując Levasa jako aplikację
w Microsoft Entra ID (dawniej Azure Active Directory).

> **Uwaga.** Rejestrację zwykle robi administrator szkolnego Microsoft 365. W wielu szkołach może ją zrobić także
> nauczyciel – jeśli w kroku 2 zobaczysz „brak uprawnień”, poproś administratora o kroki 1–5 i przekazanie
> trzech wartości z kroków 3 i 4.

---

## 0. Pod jakim adresem działa gra?

Microsoft po zalogowaniu odsyła ucznia na **adres zwrotny** Levasa. Musi on zgadzać się co do znaku z tym,
co wpiszesz w kroku 2, i – poza komputerem lokalnym – zaczynać się od `https://`.

| Sytuacja | Adres gry w przeglądarce | Adres zwrotny do wpisania |
|---|---|---|
| Próba na własnym komputerze | `http://localhost:8766` | `http://localhost:8766/konta/microsoft/login/callback/` |
| Gra na szkolnym serwerze z certyfikatem | `https://levas.szkola.pl` | `https://levas.szkola.pl/konta/microsoft/login/callback/` |

Można wpisać oba adresy naraz (jedna aplikacja, kilka adresów zwrotnych).

> **Uwaga.** Adres w sieci szkoły typu `http://192.168.1.20:8765` **nie zadziała** – Microsoft przyjmuje
> `http://` tylko dla `localhost`. Do gry całej klasy z kontami Microsoft potrzebny jest serwer z adresem
> `https://` (ustawia go informatyk szkoły – zob. punkt 7). Do tego czasu klasa może grać na loginach i hasłach.

## 1. Wejdź do Microsoft Entra

1. Otwórz **https://entra.microsoft.com** i zaloguj się szkolnym kontem.
2. Z lewej: **Identity → Applications → App registrations** (po polsku: *Tożsamość → Aplikacje → Rejestracje
   aplikacji*).

## 2. Zarejestruj aplikację

1. Kliknij **New registration** (*Nowa rejestracja*).
2. **Name:** `Levas`.
3. **Supported account types:** *Accounts in this organizational directory only* (tylko konta tej szkoły).
4. **Redirect URI:** platforma **Web**, adres zwrotny z tabeli w punkcie 0.
5. Kliknij **Register**.

## 3. Skopiuj dwa identyfikatory

Na stronie aplikacji (**Overview** / *Przegląd*) skopiuj do notatnika:

- **Application (client) ID** – identyfikator aplikacji,
- **Directory (tenant) ID** – identyfikator dzierżawy szkoły.

Wyglądają tak: `1b2c3d4e-0000-1111-2222-333344445555`.

## 4. Utwórz klucz tajny

1. **Certificates & secrets → Client secrets → New client secret**.
2. Opis: `Levas`, ważność: 12 albo 24 miesiące. Kliknij **Add**.
3. Od razu skopiuj kolumnę **Value** (nie *Secret ID*!) – po odświeżeniu strony nie da się jej już podejrzeć.

> **Uwaga.** Klucz tajny jest jak hasło: nie wysyłaj go mailem do uczniów, nie wklejaj na czacie i nie wrzucaj
> do repozytorium. Po wygaśnięciu (np. za rok) utwórz nowy i podmień go w punkcie 6.

## 5. Uprawnienia (zwykle nic do zrobienia)

W **API permissions** powinno już być **Microsoft Graph → User.Read** (odczyt imienia, nazwiska i adresu).
Levas nie potrzebuje niczego więcej. Jeśli przy pierwszym logowaniu uczeń zobaczy „Potrzebna zgoda
administratora”, administrator klika tu **Grant admin consent for …** (*Udziel zgody administratora*).

## 6. Wpisz dane do Levasa

W folderze `gra` jest plik `lokalne.json` (powstaje przy pierwszym uruchomieniu; nie trafia do gita). Otwórz go
Notatnikiem i dopisz sekcję `microsoft` – przecinek po poprzedniej linii jest ważny:

```
{
 "secret_key": "…zostaw bez zmian…",
 "microsoft": {
  "client_id": "Application (client) ID z kroku 3",
  "tenant": "Directory (tenant) ID z kroku 3",
  "secret": "Value z kroku 4"
 }
}
```

Zamiast pliku można ustawić zmienne środowiskowe `LEVAS_MS_CLIENT_ID`, `LEVAS_MS_TENANT` i `LEVAS_MS_SECRET`
(wygodne na serwerze). Zmienne mają pierwszeństwo przed plikiem.

**Próba na własnym komputerze.** `start.bat` loguje się sam na lokalne konto mistrza gry, więc strony logowania
nie widać. Do próby uruchom w folderze `gra` serwer z logowaniem na porcie 8766:

```
.venv\Scripts\python manage.py runserver 8766
```

i otwórz **http://localhost:8766** (właśnie `localhost`, nie `127.0.0.1` – adres musi się zgadzać z krokiem 2).
Na stronie logowania pojawi się przycisk Microsoft.

## 7. Serwer szkolny z https (dla informatyka)

- Levas za serwerem WWW z certyfikatem (np. nginx, IIS, Caddy) przekazującym ruch do Django i nagłówek
  `X-Forwarded-Proto: https`.
- Ustawienia (zmienne środowiskowe albo `lokalne.json`):
  - `LEVAS_HOSTY=levas.szkola.pl` albo `"hosty": ["levas.szkola.pl"]` – adres serwera,
  - `LEVAS_HTTPS=1` albo `"https": true` – adresy zwrotne z https, bezpieczne ciasteczka,
  - `LEVAS_DEBUG=0` – bez stron diagnostycznych Django.
- W aplikacji Microsoft (krok 2, **Authentication**) dopisz adres zwrotny
  `https://levas.szkola.pl/konta/microsoft/login/callback/`.

## 8. Role i drużyny

- **Pierwsze logowanie kontem Microsoft zakłada konto ucznia** (imię i nazwisko z konta szkolnego).
- **Nauczyciel jako mistrz gry:** zaloguj się raz kontem Microsoft, potem w folderze `gra`:

  ```
  .venv\Scripts\python manage.py konto anna.kowalska@szkola.edu.pl --mg
  ```

  (adres e-mail wskazuje konto założone przez Microsoft). Rolę można też nadać w panelu **Konta** (`/admin/`):
  użytkownik → grupa `mistrz_gry`.
- **Uczniowie w drużynach:** niech każdy uczeń zaloguje się raz; potem mistrz gry dopisuje ich w zakładce
  *Drużyny* gry, wybierając z listy kont (nie trzeba zakładać kont z hasłami).
- Konta z loginem i hasłem działają dalej obok kont Microsoft.

## Gdy coś nie działa

| Komunikat | Przyczyna i rada |
|---|---|
| Brak przycisku Microsoft | Levas nie widzi `client_id` – sprawdź `lokalne.json` (przecinki, cudzysłowy) i uruchom serwer ponownie. |
| `AADSTS50011` … *redirect URI* | Adres zwrotny nie zgadza się z krokiem 2 – inny port, `127.0.0.1` zamiast `localhost`, brak `/` na końcu albo `http` zamiast `https`. |
| `AADSTS7000215` … *invalid client secret* | Skopiowano *Secret ID* zamiast *Value* albo klucz wygasł – krok 4. |
| `AADSTS50194` … *not configured as a multi-tenant application* | Brak `tenant` w `lokalne.json` – wpisz Directory (tenant) ID z kroku 3. |
| `AADSTS50020` … *does not exist in tenant* | Konto spoza szkoły (np. prywatne Outlook) – logują się tylko konta tej dzierżawy. |
| „Potrzebna zgoda administratora” | Krok 5: *Grant admin consent*. |
| `DisallowedHost` / „Bad Request (400)” | Adres serwera nie jest w `hosty` / `LEVAS_HOSTY` – punkt 7. |
