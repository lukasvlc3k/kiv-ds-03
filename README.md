# KIV/DS Úkol 03 - ZooKeeper a distribuované key-value úložiště


## Postup řešení
Při spuštění nodu (klienta) dojde nejprve k inicializaci spojení se zookeeperem a zaregistrování nodu na patřičné místo v hierarchické struktuře (ve formě binárního stromu).

Pokud je node označen jako root (parametr v ENV), vytvoří v ZK uzel pojmenovaný /root. Pokud není root, najde (pomocí BFS) první neúplný node, tedy node, který má pouze jednoho potomka, a zaregistruje se hierarchicky pod něj. K označení uzlů se používá sekvenční číslování zajištěné Zookeeperem (prefix child), abych se vyhl problémům s případnou duplicitou.
V případě, že by se ale spustilo více nodů zároveň, mohlo by teoreticky dojít k nesprávnému vyvážení stromu. Nicméně protože Vagrant jednotlivé nody spouští postupně, tento problém v rámci této úlohy neřeším.

Po inidializaci spojení se ZK a zaregistrování uzlu, node spustí webový server poskytující REST API rozhraní.

Rozhraní nabízí 3 příkazy - GET, PUT a DELETE, fungující dle specifikace v zadání.

- GET je dostupný na cestě /key/{key}
- PUT na /key/{key} (s tím, že v body (json) očekává položku value)
- DELETE na /key/{key}

## Využité technologie:
- flask_openapi3 (webový server, postavený na Flasku, který umožňuje snadné vygenerování OpenAPI dokumentace)
- knihovny requests a pydantic

## Nastavení
V rámci nastavení je důležité zmínit především položku <code>LEVELS_COUNT</code> ve Vagrantfile. Ta nastavuje počet vrstvev a tím i počet nodů, které budou spuštěny. Dalším nastavitelným parametrem je číslo root nodu (<code>ROOT_NODE_NUMBER</code>). Výchozí hodnoty: 3 úrovně a root node = 2.

Pro snazší testování (OpenAPI) všechy servery publikují svůj port s HTTP REST API do host systému.

## Spuštění
<code>vagrant up</code> spustí celý systém

## CLI klient
### Generování
Klienta je možné jednoduše vygenerovat na základě předpisu z OpenAPI. K tomuto účelu jsem použil knihovnu openapi-python-client, nicméně neměl by být problém klienta vygenerovat ani za použití jiné knihovny.

Instalaci knihovny je možné provést příkazem:
<code>pip install openapi-python-client</code>

A následné vygenerování pak <code>openapi-python-client generate --url http://[endpoint včetně portu]/openapi/openapi.json</code> (v projektu je ponechána výchozí cesta k openapi.json souboru - tedy /openapi/openapi.json).

Případně je možné klienta vygenerovat ze souboru openapi.json, který je přiložen ve složce cli_client (příkazem <code>openapi-python-client generate --path .\cli_client\openapi.json</code>).

Po zadání některého z výše uvedených příkazů pro generování vznikne složka, jejíž název odpovídá nadřazené složce (bohužel se mi nepovedlo najít způsob, jak v příkazu "output directory" specifikovat).

Pro správné fungování klienta je potřeba obsah této složky zkopírovat do cli_client/generated (tak, aby existovala cesta cli_client/generated/api atd.). Aktuální verze nicméně obsahuje vygenerovaného klienta dle aktuální specifikace.

### Spuštění a testování
Příkazem <code>python cli_client/cli.py [endpoint]</code> spustíte CLI rozhraní, které umožní snadné ověření fungování systému.

Po spuštění můžete ve smyčce psát příkazy po potvrzení (enterem) vidíte výsledek jejich provedení.

Podporované příkazy:
- GET {key} (například GET test)
- PUT {key} {value} (například PUT test ahoj)
- DELETE {key} (například DELETE test)
- HELP (pro vypsání nápovědy)


## Cache coherence

Myslím, že je několik možných postupů, jak koherenci cache v tomto případě zajistit. Použité řešení závisí na několika faktorech, zde zmíním ty, které považuji za nejdůležitější:

- rychlost konvergence: tedy jak rychle po provedení změny je potřeba mít v celém systému správné (nové) hodnoty. Tento faktor rozhoduje o tom, zda je potřeba změny provádět nějakým způsobem okamžitě, nebo nevadí nějaké zpoždění
- velikost dat: faktor určující, jak velký problém pro nás je přenášet data i v případě, že to není nezbytně nutné (v případě velkých dat to může být komplikovanější)
- jak moc je důležité zajistit, aby nikdo nemohl přečíst starší data


Napadají mě 3 hlavní řešení:
- timeout: každý záznam by měl nějakou dobu platnosti, v momentě, kdy by vypršela, požádal by nadřazený node o aktuální data (víceméně podobným způsobem, jako funguje TTL u DNS) - pomalejší a nezajišťuje aktuálnost, přenosy dat závisí na způsobu implementace

- okamžité probublání: ihned po operaci, co upravuje data (PUT, DELETE) by se zajistila distribuce aktualizace na všechny nody (v podstatě zneplatnění původního záznamu a nahrazení novou hodnotou). To je řešitelné například tak, že kromě distribuce směrem nahoru by docházelo k distribuci po vrstvách. Bylo by ale potřeba zajistit, aby se zprávy neduplikovaly, například tím, že směrem nahoru bude posílat pouze ten, který se o změně dozvěděl z celé vrstvy jako první. Případně možno nastavit omezení, že změny musí být realizovány jen na root (master) uzlu a ten pak zajistí aktualizaci směrem ke svým potomkům.

- periodická aktualizace: vlastně stejný princip, jako u metody "timeout", jen by k aktualizaci docházelo shora - nadřazený node by jednou za čas poskytl svým potomkům aktuální data, bez ohledu na to, zda je potřebují či nikoliv