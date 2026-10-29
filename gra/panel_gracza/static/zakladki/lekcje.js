// Opisy dydaktyczne do zakładek finansów (P7): jak to działa w prawdziwej firmie. Zwinięte – nie zasłaniają decyzji.
import { esc, lekcja, zl } from "./wspolne.js";

// Samodzielna księgowość (gra z lokalami): co po kolei zrobić z dokumentami i deklaracjami. Reguły kolumn –
// silnik/ksiegowosc/biuro.py (WYJASNIENIA); otwarta, dopóki nic nie zaksięgowano.
export function krokiKpir(K, otwarta) {
  const kolumny = Object.entries(K.wyjasnienia || {}).map(([k, w]) => `<li><b>${esc(K.kolumny[k] || k)}</b> – ${esc(w)}</li>`).join("");
  const html = lekcja("Jak samemu wypełnić KPiR i deklaracje – krok po kroku", [
    `<b>1. Weź dokumenty z poprzedniej rundy.</b> W tabeli niżej jest każdy dokument tamtej rundy: faktury, rachunki, wyciągi
     i umowy. „+” to pieniądze, które wpłynęły do firmy, „−” – te, które wypłynęły.`,
    `<b>2. Każdemu dokumentowi wybierz kolumnę KPiR.</b> Zadaj sobie pytanie: czy to przychód, koszt, czy ani jedno, ani drugie?<ul>${kolumny}</ul>`,
    `<b>3. Wybierz stawkę VAT.</b> Taką, jaka jest na dokumencie dla tego towaru albo usługi. Dokument bez VAT (np. wyciąg,
     umowa, przelew do urzędu) – 0%. Faktura z kilkoma stawkami ma je już rozpisane – tam nic nie wybierasz.`,
    `<b>4. Sprawdź, czy zaksięgowano wszystko.</b> Nad tabelą widać, ile dokumentów z ilu ma kolumnę – każdy musi ją mieć.`,
    `<b>5. Policz deklaracje.</b> Tabela „Z Twoich zapisów” liczy je z Twoich wpisów: dochód = przychody − koszty,
     VAT do zapłaty = należny − naliczony − nadwyżka z poprzedniej rundy, zaliczka PIT od dochodu narastająco minus zaliczki już wpłacone,
     składka zdrowotna od dochodu (najmniej minimalna).`,
    `<b>6. Wpisz kwoty w deklaracjach do urzędu.</b> Przepisz je ręcznie albo przyciskiem „Przepisz kwoty wyliczone z zapisów”.`,
    `<b>7. Wyślij decyzje rundy.</b> Deklaracje idą razem z nimi. Przy przeliczeniu urząd je sprawdzi: różnicę dopłacisz
     albo odzyskasz, a za każdą pomyloną deklarację zapłacisz mandat ${zl(K.samodzielna.kara_blad)}. Co poszło nie tak –
     zakładka z wynikami biura w następnej rundzie.`,
  ]);
  return otwarta ? html.replace('<details class="lekcja">', '<details class="lekcja" open>') : html;
}

export const LEKCJA_VAT = lekcja("Jak działa VAT – w grze i naprawdę", [
  `<b>VAT płaci klient, firma go tylko „przenosi”.</b> Ze sprzedaży zbierasz VAT należny, przy zakupach płacisz dostawcom
   VAT naliczony, a do urzędu oddajesz różnicę. Dlatego VAT nie jest ani Twoim przychodem, ani kosztem.`,
  `<b>Przykład:</b> kebab za 32,40 zł brutto przy stawce 8% to 30,00 zł netto + 2,40 zł VAT. Składniki do niego za 10,80 zł
   brutto (8%) zawierają 0,80 zł VAT. Do urzędu idzie 2,40 − 0,80 = <b>1,60 zł</b>.`,
  `<b>Stawki zależą od towaru.</b> W Polsce posiłki w gastronomii mają zwykle 8%, ale np. napoje alkoholowe 23% –
   dlatego cena brutto tego samego „zysku” bywa różna.`,
  `<b>Nadwyżka:</b> gdy naliczony jest większy od należnego (np. po dużych zakupach sprzętu), różnica przechodzi na
   kolejny okres. W prawdziwej firmie można też poprosić urząd o zwrot.`,
  `<b>Naprawdę:</b> czynny podatnik VAT co miesiąc (albo kwartał) wysyła plik JPK_V7 do 25. dnia następnego miesiąca.
   Firma z małą sprzedażą (do 200 000 zł rocznie) może być zwolniona z VAT – ale wtedy nie odliczy go od zakupów.`,
]);

export const LEKCJA_KPIR = lekcja("Czym jest KPiR i co z niej wynika", [
  `<b>KPiR</b> (podatkowa księga przychodów i rozchodów) to najprostsza księgowość dla jednoosobowej działalności i małych
   spółek osobowych. Każde zdarzenie gospodarcze to jeden wpis: data, opis i kwota w odpowiedniej kolumnie.`,
  `<b>Dochód = przychody − koszty.</b> Podatek PIT płaci się od dochodu, nie od przychodu – dlatego każdy udokumentowany
   koszt firmy obniża podatek.`,
  `<b>Dochód to nie gotówka.</b> Sprzęt drogi (środek trwały) wchodzi w koszty stopniowo, przez amortyzację; spłata kapitału
   kredytu nie jest kosztem (odsetki są); wypłata pieniędzy przez właściciela też nie jest kosztem.`,
  `<b>Towar to koszt w dniu zakupu</b> – nawet gdy jeszcze leży w chłodni. Na koniec roku robi się spis z natury (remanent),
   który wyrównuje różnicę.`,
  `<b>Kwoty są netto:</b> VAT żyje w osobnym rejestrze (zakładka VAT).`,
]);

export const LEKCJA_PIT_ZUS = lekcja("PIT i ZUS przedsiębiorcy – w skrócie", [
  `<b>PIT liniowy (19%)</b> liczy się od dochodu. Zaliczki płaci się narastająco: podatek od dochodu od początku roku minus
   zaliczki już wpłacone. Strata w jednym miesiącu zmniejsza podatek w kolejnych.`,
  `<b>Składka zdrowotna</b> przy podatku liniowym to 4,9% dochodu, ale nie mniej niż ustawowe minimum. Część zapłaconej
   zdrowotnej można odliczyć od dochodu – do limitu rocznego (widać go wyżej).`,
  `<b>ZUS społeczny</b> (emerytalna, rentowa, wypadkowa, dobrowolnie chorobowa, Fundusz Pracy) to koszt firmy, więc obniża PIT.
   Nowa firma ma <b>ulgę na start</b> (6 miesięcy bez składek społecznych), potem 24 miesiące <b>preferencyjnego ZUS</b>
   (od 30% płacy minimalnej), a dopiero później pełny ZUS.`,
  `<b>Pracownik kosztuje więcej niż jego pensja brutto:</b> pracodawca dopłaca swoje składki ZUS (około 20% pensji).
   Z kolei z pensji brutto pracownika potrąca się jego składki i zaliczkę PIT – zostaje mu „na rękę”.`,
  `<b>Terminy naprawdę:</b> ZUS do 20. dnia miesiąca, zaliczka PIT do 20. dnia następnego miesiąca, zeznanie roczne PIT-36L
   do 30 kwietnia.`,
]);

export const LEKCJA_BANK = lekcja("Konto, lokata i kredyt – na co patrzeć", [
  `<b>Konto firmowe</b> kosztuje: opłata za konto, za kartę, czasem za przelewy. Porównuj banki po pełnym koszcie miesięcznym,
   nie po jednej opłacie z reklamy.`,
  `<b>Lokata:</b> oprocentowanie podaje się w skali roku. Pieniądze na lokacie są bezpieczne, ale zamrożone – nie zapłacisz
   nimi dostawcy. Naprawdę od odsetek bank pobiera 19% podatku (tzw. podatek Belki).`,
  `<b>Kredyt:</b> liczy się nie tylko oprocentowanie, ale też prowizja i opłaty – wszystko razem pokazuje <b>RRSO</b>.
   Raty równe są na początku lżejsze, raty malejące – tańsze w sumie.`,
  `<b>Kredyt odnawialny</b> (limit w rachunku) bank uruchamia sam, gdy zabraknie pieniędzy na koncie. Wygodny, ale zwykle droższy
   od kredytu na konkretny cel – odsetki płacisz od wykorzystanej kwoty.`,
  `<b>Zdolność kredytową</b> bank ocenia po przychodach, historii spłat i zabezpieczeniach. Dlatego nowej firmie trudno
   o duży kredyt – a ktoś, kto pożycza „od ręki, bez pytań” (jak Harpagon), bierze za to znacznie więcej, niż pozwala
   ustawowy limit odsetek maksymalnych.`,
]);

export const LEKCJA_RAPORT = lekcja("Zysk to nie to samo co pieniądze na koncie", [
  `<b>Rachunek zysków i strat</b> pokazuje, czy firma zarabia; <b>przepływy pieniężne</b> – czy ma czym zapłacić. Firmy
   częściej upadają z braku gotówki niż z braku zysku.`,
  `<b>Przykład:</b> kupujesz grill za 20 000 zł – gotówka spada od razu, ale koszt w księgach rozkłada się na lata. Bierzesz
   kredyt – gotówka rośnie, a zysk się nie zmienia.`,
  `<b>Próg rentowności:</b> koszty stałe (czynsz, pensje, abonamenty) podzielone przez marżę na jednej porcji (cena netto
   minus koszt składników) mówią, ile porcji trzeba sprzedać, żeby wyjść na zero.`,
  `<b>Na co patrzeć co rundę:</b> saldo konta (czy starczy na pensje i czynsz), dochód netto (czy model biznesowy działa)
   i zadłużenie (czy nie rośnie szybciej niż sprzedaż).`,
]);
