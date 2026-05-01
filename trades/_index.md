\# 🟣 Sexta-Feira — Dashboard



> \[!LIVE] Trades Abertos Agora

```dataview

TABLE ativo, direcao, entry, stop, take, score

FROM "trades"

WHERE tipo = "trade" AND status = "OPEN"

SORT data\_abertura DESC

```



> \[!STATS] Performance Últimos 7 Dias

```dataview

TABLE 

&#x20; sum(pnl\_usdt) as PnL\_7d,

&#x20; round(avg(pnl\_usdt), 2) as Media,

&#x20; round(sum(pnl\_usdt > 0) / count(pnl\_usdt) \* 100, 1) as WinRate

FROM "trades"

WHERE tipo = "trade" AND data\_abertura >= date(today) - dur(7 days)

```



> \[!RECENT] Últimos Trades Fechados

```dataview

TABLE ativo, direcao, pnl\_usdt, score, status

FROM "trades"

WHERE tipo = "trade" AND status != "OPEN"

SORT data\_fechamento DESC

LIMIT 10

```

