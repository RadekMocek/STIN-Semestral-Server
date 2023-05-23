# 🏦

[![codecov](https://codecov.io/gh/RadekMocek/STIN-Semestral-Server/branch/develop/graph/badge.svg?token=SOF8C73407)](https://codecov.io/gh/RadekMocek/STIN-Semestral-Server) / 70%

## Rozšíření

```txt
pokud má uživatel účet v dané měně a na něm dostatek peněz:
    * provést platbu z daného účtu – odečíst peníze
jinak pokud má uživatel účet v dané měně a něm dostatek peněz včetně povoleného kontokorentu 10 %:
    * provést platbu z daného účtu – odečíst peníze
    * provést jednorázový úrok 10 %
jinak:
    * převést částku na CZK
    pokud má uživatel dostatek peněz na CZK účtu:
        * provést platbu z CZK účtu – odečíst převedené peníze
    jinak pokud má uživatel dostatek peněz na CZK účtu včetně povoleného kontokorentu 10 %:
        * provést platbu z daného účtu – odečíst peníze
        * provést jednorázový úrok 10 %
    jinak:
        * platba se neprovede
```
