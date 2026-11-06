// Giełda (UF15): miejsce na giełdę, którą dostarczy kolega razem z nową mapą – na razie tylko tablica „w budowie”.
export const W_BUDOWIE = (tekst) => `<div class="w-budowie" role="note"><span class="tasma"></span>
  <div class="napis"><b>W budowie</b><span>${tekst}</span></div><span class="tasma"></span></div>`;

export const gielda = {
  tytul: "Giełda", tytulPelny: "Właściciel – giełda", ikona: "wykres",
  info: "Tu właściciel będzie mógł zainwestować prywatne pieniądze w akcje lubelskich spółek. Na razie trwa budowa.",
  decyzje() {
    return W_BUDOWIE("Giełda papierów wartościowych otwiera się wkrótce. Robotnicy właśnie montują tablicę z notowaniami – "
      + "Koziołek pilnuje, żeby nikt nie kupił akcji przed otwarciem.");
  },
};
