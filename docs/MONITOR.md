# Мониторинг аренды (Барселона и окрестности до Таррагоны + Кастельон-де-ла-Плана с пригородами, с 2026-11-16): инструкция запуска

Цель: найти новые объявления, добавить их в `state.json`, пересобрать страницу-артефакт и PDF, отправить пуш, если есть новые.
Критерии: 500-1000 €/мес, строго с мебелью (Idealista: отсеивать «дом без мебели»; в скрипте уже учтено), квартира или студия целиком, Барселона и окрестности максимум до Таррагоны, а также Кастельон-де-ла-Плана и пригороды (Бенисасим, Бурриана, Вила-Реал). Дальше от Барселоны (Таррагона, Гарраф/Пенедес, Кастельон) страница по умолчанию показывает только с мебелью и парковкой (Бахо-Льобрегат, Маресме, Вальес, Гарраф/Пенедес, Таррагона и побережье). Районы с оценкой ≤2 отбрасываются при ingest. Старые квартиры Валенсии и Кастельона в `state.json` помечены `archived: true` и не выводятся. Города и районы: `bcn_zones.py` (пригороды) и `ZB` в `rooms.py` (Барселона). Объявления «с декабря и позже» идут в отдельный раздел.

Артефакт (телефон): https://claude.ai/artifact/LKopYegeDswvZchXhvQo4M (публиковать файл `../arenda_mobile.html` с параметром `url`).
Файлы лежат в `~/Documents/AI/Claude/Projects/Rent/` (папка `monitor/` со скриптами и `state.json`).

## Один цикл (делать по порядку, коротко)

1. `mcp__claude-in-chrome__tabs_context_mcp`. Нужны 5 вкладок: Idealista, Pisos.com, yaencontre, Milanuncios, Fotocasa.
   Если вкладок нет (или у вкладки другой сайт), создать через `tabs_create_mcp`, открыть главный адрес сайта (ниже) и установить скрипт:
   `cd ~/Documents/AI/Claude/Projects/Rent/monitor && python3 monitor.py scan <idealista|pisos|yaencontre|milanuncios|fotocasa>`
   и выполнить напечатанный код в вкладке через `javascript_tool` (код сам сохранится в `localStorage.rentScan` и запустится).
2. В каждой вкладке запустить сохранённый скрипт одной командой (не вставлять код заново):
   `eval('('+localStorage.getItem('rentScan')+')')()` через `javascript_tool` (вернёт промис, скрипт работает в фоне), потом ждать 20-60 с и читать
   `window.__sc.done + ' ' + window.__sc.out.length`. Пока `done` не `true`, ждать (`computer wait`, до 10 с за раз). Лимит `javascript_tool` 45 с: код не ждать, только запускать и опрашивать.
   - Idealista, Pisos.com, yaencontre: адрес вкладки не важен (скрипт сам делает запросы), главное чтобы вкладка была на домене сайта.
   - Idealista, Pisos.com, yaencontre: адрес вкладки не важен, главное домен сайта; скрипты сами обходят список городов (Барселона + пригороды до Таррагоны).
   - Milanuncios: открыть по очереди `https://www.milanuncios.com/alquiler-de-pisos-en-barcelona-barcelona/?desde=500&hasta=1000&amueblado=1`, затем `.../alquiler-de-pisos-en-tarragona/?desde=500&hasta=1000` (пригороды: `...-en-hospitalet-de-llobregat/`, `-en-badalona/`, `-en-sabadell/`, `-en-terrassa/`, `-en-mataro/`, `-en-sant-cugat-del-valles/`); на каждой запускать скрипт.
   - Fotocasa: `https://www.fotocasa.es/es/alquiler/viviendas/barcelona-capital/todas-las-zonas/l?minPrice=500&maxPrice=1000&sortType=publicationDate`, затем `.../tarragona-capital/...`, `.../l-hospitalet-de-llobregat/...`, `.../badalona/...`; на каждой запускать скрипт. Если всплыло окно подписки, нажать «Нет, спасибо».
3. Забрать результат: в вкладке выполнить
   `document.body.innerHTML='<article><pre>'+window.__sc.tsv.replace(/</g,'&lt;')+'</pre></article>';window.__sc.tsv.length`
   и вызвать `get_page_text` (возвращает строки вида `site¦ref¦addr¦price¦rooms¦m2¦lift¦temp¦avail¦url`). Если `tsv` пустой, новых нет. Склеить строки всех сайтов в файл
   `~/Documents/AI/Claude/Projects/Rent/monitor/inbox/YYYY-MM-DD_HHMM.tsv` (создать папку `inbox`).
   Ограничение: после этого шага страница вкладки испорчена, это нормально, скрипт хранится в localStorage; для Milanuncios/Fotocasa страница всё равно открывается заново.
4. `python3 monitor.py ingest inbox/<файл>.tsv`
   - Скрипт сам сопоставит район, оценку, транспорт и ссылки на источники, объединит дубли с других сайтов, отправит в раздел «с декабря» объявления с датой въезда декабрь/январь/февраль в тексте (поле `avail`).
   - Просмотреть напечатанные «+» строки: если в `avail` написано, что сдают позже, а метки `defer` нет, исправить в `state.json` (`deferred: true`, `avail_note`).
   - Явный мусор (юридические дубли, площадь 300 м² и т.п.) можно удалить из `state.json` или пометить `gone: true`.
5. Фото и карты (страница не грузит внешние картинки, поэтому всё упаковывается в файлы): `python3 geo.py` (координаты новых карточек, кэш geo.json), затем `python3 monitor.py build`, затем `.venv/bin/python pack.py --redo-empty` (скачивает до 4 фото и рисует карту для новых карточек в `pub/p/<id>.json`, для Pisos.com и Fotocasa ищет фото сам; для Idealista и yaencontre фото берутся из `photos/*.json`, при отсутствии их нет). Затем снова `python3 monitor.py build` (обновит индекс фото).
5b. `python3 monitor.py build` (создаёт `../arenda_mobile.html` и `../arenda_polnyj_poisk.pdf/.html`).
6. Опубликовать: `Artifact` с `file_path=/Users/misharenne/Documents/AI/Claude/Projects/Rent/arenda_mobile.html`, `url=https://claude.ai/artifact/LKopYegeDswvZchXhvQo4M`, `root=/Users/misharenne/Documents/AI/Claude/Projects/Rent/monitor/pub` и `files` со списком новых `p/<id>.json` (старые остаются на сервере; список: `ls pub/p`). Пометки пользователя (смотрел/нет/да) лежат в db страницы, коллекция `marks`, их не трогать; capabilities не менять (db уже заявлен).
7. Если `python3 monitor.py summary` показывает «new today» больше нуля (новые не из раздела «позже»), отправить пуш (`PushNotification`): «Новых объявлений: N» и 1-3 лучших (район, цена, комнаты). Если новых нет, пуш не слать.
8. Ответить пользователю одной строкой: время, сколько найдено новых, сколько ушло в «с декабря». Не пересказывать весь список.

## Парковка, мебель и телефоны (с 2026-11-16)
Поля карточки: `furn` (yes/no/?), `park` (incl включена в цену / extra за доплату / yes есть, цена неизвестна / no / ?), `parkn` (цена доплаты), `phone` (9 цифр).
- Скрипты Idealista и yaencontre добавляют в поле avail метку `[P:I|N|Y|?]`; `monitor.py ingest` превращает её в `park`. Остальным нужен шаг `python3 enrich/enrich.py` (запускать после ingest, до geo/build): он сам заходит на страницы Pisos.com и Fotocasa, берёт парковку, мебель и телефон объявления.
- Телефоны берутся только из кода страницы (Pisos.com, Fotocasa) или текста объявления. Idealista и yaencontre прячут номер за кнопкой «Показать телефон»; её не нажимать (это засчитывается как контакт с арендодателем). Номер в форме Idealista («Ваш телефон», `phoneNumber`) принадлежит пользователю, а не арендодателю; не использовать и не сохранять.
- На странице: фильтры «С парковкой», «Мебель подтверждена», «Далеко от Барселоны: только с мебелью и парковкой» (включён по умолчанию), раздел «Мои «Да»» собирает лайкнутое со ссылками и телефонами.
- Кастельон: сканируются Idealista (`castellon-de-la-plana-castello-de-la-plana-castellon`), Pisos.com (`castellon_de_la_plana`), Fotocasa (страница `castellon-de-la-plana-castello-de-la-plana`), yaencontre (`castellon-provincia`).
- Chrome может перевести страницы сайтов на русский (адреса и названия в выдаче искажаются): при приёме проверять `zone`; для Fotocasa класть строки JSON с явным `zone`, `furn`, `park` (см. inbox/2026-11-16b_fotocasa_cast.jsonl).

## Правила и ограничения
- Первый проход 2026-11-05/06 загружен как база (`first_seen=2026-11-05`), «новыми за день» считаются объявления, впервые найденные сегодня.
- Расписание: каждые 2 часа с 8:00 до 22:00 по времени Испании (сессия должна быть открыта, Mac не спит, Chrome с расширением включён). Задача живёт 7 дней, потом нужно продлить.
- Не нажимать «Связаться», не писать арендодателям и не добавлять в избранное без явной просьбы пользователя.
- Если сайт вернул капчу или пустой список несколько запусков подряд, сообщить пользователю, не обходить защиту.
- Раз в сутки (первый запуск после 8:00) проверить, что ссылки новых объявлений открываются; снятые объявления пометить `gone: true`.

## Снятые объявления (удалять из списка автоматически)
- В каждом цикле (минимум раз в сутки, для yaencontre/Pisos/Idealista) проверять живые ссылки: `python3 monitor.py urls <домен>` печатает активные адреса. В вкладке этого сайта запустить async-скрипт: `fetch(путь)` по каждому адресу с паузой 250 мс, статус 404/410 = объявление снято (результат собирать в `window.__chk.bad`, опрашивать). Снятые адреса записать в файл и выполнить `python3 monitor.py gone <файл>`; они пропадают из списка при `build`.
- Проверено 2026-11-06: yaencontre (404 надёжно определяет снятое). Pisos/Idealista проверять осторожно (возможна защита от ботов; при капче остановиться).

## Комнаты (Барселона, Валенсия, Кастельон), до 500 €, срок от 1 месяца
Отдельный блок в той же странице (раздел «Комнаты»), своё состояние `rooms.json`, свой модуль `rooms.py`. Делать после квартир, в том же запуске.
Источники: Idealista (комнаты), Pisos.com (habitaciones), Fotocasa (compartir pisos), Milanuncios (pisos compartidos). yaencontre комнат не имеет. Хранится в localStorage вкладки под ключами `roomScan` и `roomSeen` (квартирные `rentScan`/`rentSeen` не трогать).
1. Скрипты: `cd monitor && python3 rooms.py scan idealista|pisos|fotocasa|milanuncios` печатает готовый JS. Если в `localStorage.roomScan` пусто, вставить напечатанный код в вкладку (он сохранится и запустится). Иначе запускать `eval('('+localStorage.getItem('roomScan')+')')()`.
   - Idealista и Pisos.com: один запуск делает все 3 города (вкладка на домене сайта).
   - Fotocasa: открыть по очереди `https://www.fotocasa.es/es/compartir/pisos/barcelona-capital/todas-las-zonas/l?maxPrice=500&sortType=publicationDate`, потом `valencia-capital`, потом `castellon-de-la-plana-castello-de-la-plana`; на каждой странице запускать скрипт (город определяется по адресу страницы).
   - Milanuncios: `https://www.milanuncios.com/pisos-compartidos-en-barcelona-barcelona/?hasta=500`, затем `…-en-valencia-valencia/…`, затем `…-en-castellon/…`; на каждой запускать скрипт.
2. Опрашивать `window.__sc.done`, затем `window.__sc.tsv.length` и `window.__sc.bad`. Скрипт сам убирает плохие районы и ночные сроки больше 1 месяца.
3. Забрать результат: `document.body.innerHTML='<article><pre>'+window.__sc.tsv.replace(/</g,'&lt;')+'</pre></article>'`, затем в вкладке кликнуть, `cmd+a`, `cmd+c`, и в терминале `pbpaste > inbox/rooms_<сайт>_<город>_raw.txt` (так не нужно перепечатывать данные; get_page_text для комнат не использовать, он слишком длинный). Строки: `site¦ref¦city¦addr¦price¦minstay¦free¦url¦B|desc` (B = P свой санузел, S общий, U не указан; плюс F/M для «только девушкам/парням»). Сокращения в url: `@P`, `@M`, `@F` раскрываются сами.
4. `python3 rooms.py ingest inbox/<файл>.tsv` (можно склеить несколько файлов через `cat`). Он классифицирует район, убирает плохие (оценка 1-2, затопление, наркоторговля, промзоны, не Барселона/пригород, район Барселоны не определён), считает «свободно позже» (дата въезда позже +35 дней) и санузел по тексту.
5. `python3 monitor.py build` (включает комнаты), публикация артефакта как обычно. Пуш про комнаты только если `python3 rooms.py summary` показывает новые за сегодня (`new today`, кроме первого дня 2026-11-06).
Ограничения: Fotocasa и Milanuncios читают только первые ~30-40 карточек на город, Idealista и Pisos.com до 4 страниц. Санузел определяется по тексту объявления, на Idealista почти никогда не указан, поэтому большинство комнат идёт как «санузел не указан».
Районы Барселоны: таблица `ZB` в `rooms.py` (оценка 1-5 с источниками). Оценка ≤2 исключается. Valencia/Castellón используют те же районы, что квартиры.

Правило «вдвоём» (добавлено 2026-11-06): скрипты комнат определяют, можно ли заехать парой (третий символ кода: Y можно, N нельзя, ? не указано). Комнаты с N (нельзя парам, для одного человека) отбрасываются при ingest; Y помечаются «можно вдвоём» и фильтруются кнопкой «Точно можно вдвоём». Если в объявлении ничего не сказано, комната остаётся с пометкой «вдвоём: не указано».
Скрипты теперь универсальные (без зашитых id): известные id берутся из `localStorage.roomSeen`. Для повторной проверки уже найденных комнат можно положить их id в `localStorage.roomOnly` (список JSON), тогда скрипт читает только их; в обычных циклах `roomOnly` должен быть пустым (`localStorage.removeItem('roomOnly')`).

## Обновление 2026-11-19 (читать первым)
- Расписание: каждый час с 8:07 до 22:07 (cron `7 8-22 * * *`, живёт 7 дней). Цикл делать так же, как выше, но ПРОВЕРЯТЬ, что отработали все источники: Idealista, Pisos.com, yaencontre, Fotocasa (Барселона), Habitaclia, Milanuncios (Habitaclia и Fotocasa: открыть страницу, запустить скрипт; для других городов см. ниже). В ответной строке перечислить число объявлений с каждого сайта.
- Habitaclia: `python3 monitor.py scan habitaclia`, страницы `https://www.habitaclia.com/alquiler/viviendas/<город>/s?minPrice=500&maxPrice=1000&sortType=publicationDate` (города: barcelona-provincia/barcelona-capital, badalona, sabadell, terrassa, mataro, sant-cugat-del-valles, granollers, vilanova-i-la-geltru, castelldefels; на каждой навигация + запуск скрипта, ~30 с). Строки идут в ingest как обычно (разделитель `¦`).
- Новая группа «Сабадель и Террасса» (`G_ST` в `bcn_zones.py`): электрички в Барселону.
- Раздел «Дома» (до 1100 €, `kind: "house"`): скрипты `python3 monitor.py scan casas_idealista|casas_pisos|casas_yae` (в localStorage вкладки под ключом `casaScan`/`casaSeen`, квартирные `rentScan` не трогать), запуск `eval('('+localStorage.getItem('casaScan')+')')()`. Idealista: путь `/ru/alquiler-viviendas/<район>/con-precio-hasta_1100,chalets/`. Pisos.com: `/alquiler/casas-<город>/` (фильтр цены в URL не работает, цена режется в скрипте). Мебель определяется меткой `[F:Y|N|?]` в поле avail. Ingest: `python3 monitor.py ingest <файл> --casa`; берутся только Барселона, Бахо-Льобрегат, Маресме, Сабадель/Террасса, Гарраф, Сант-Кугат, Серданьола, Рубí (в радиусе не дальше Террассы и вдоль моря). Домов до 1100 € мало: за цикл 0-3 новых.
- Не покрыто: Enalquiler (нет прямых ссылок), Milanuncios (нет района), Fotocasa вне Барселоны, дома на Fotocasa/Habitaclia.
- Pack: `.venv/bin/python pack.py` (не системный python3: там нет PIL). Фото для Idealista/yaencontre берутся отдельным fetch в браузере (см. details/*.json).

## Чистка неактуальных (с 2026-11-19, делать в КАЖДОМ цикле)
- Снятые объявления помечаются `gone: true` и пропадают отовсюду, включая «Мои «Да»» и «Не нравится» (страница показывает только живые карточки).
- Каждый цикл: прочитать пометки пользователя (`ArtifactData` list collection `marks` артефакта; `k` = ссылка, `s` = good/bad/seen) и проверить на живость ссылки с `s=good` (и `bad`): в вкладке сайта fetch по пути, признак снятого: Idealista/yaencontre/Pisos статус 404/410 (Idealista проверять через `/ru/inmueble/<id>/`), Fotocasa редирект с `propertyNotFound` в итоговом адресе, Habitaclia статус ≥400 или итоговый адрес без uuid. Снятые пометить `gone: true` в state.json (`python3 monitor.py urls <домен>` печатает активные адреса для полной проверки).
- Полную проверку всех ссылок (скрипты как 2026-11-19 14:00: fetch с паузой 350-500 мс) делать раз в сутки в первом цикле после 8:00.
- «Мои «Да»» теперь с фото-галереей и кнопкой «📍 Google Maps» (координаты из geo.json, для приблизительных помечено «район, примерно»).

## Студии (с 2026-11-19, добавлять в каждый цикл)
- Отдельные запуски: Idealista `.../con-precio-hasta_1000,estudios/` и Pisos.com `/alquiler/estudios-<город>/desde-500/hasta-1000/amueblado/`. В вкладке: взять `localStorage.rentScan`, заменить `rentSeen`→`studioSeen`, `rentScan`→`studioScan`, для Idealista добавить `,estudios` к `con-precio-hasta_1000`, для Pisos `/alquiler/pisos-`→`/alquiler/estudios-`, сохранить как `studioScan` и запустить `eval('('+localStorage.getItem('studioScan')+')')()`. Репо-версии: `scan/studios_idealista.js`, `scan/studios_pisos.js`.
- Много студий отсеивается: без мебели (Idealista), плохие районы (Раваль), слишком далеко.

## Фильтр «временное / студентам / врачам / госслужащим» (с 2026-11-19, ОБЯЗАТЕЛЬНО в каждом цикле)
- Критерий пользователя: временная аренда (temporada/temporal/сезонная/«до июня»/11 месяцев и т.п.), «только студентам», врачам, госслужащим — не подходит (арендодатели отказывают). Такие объявления не показывать.
- Порядок: ingest → enrich → geo → details → build → pack → **`python3 screen.py`** → build → publish. `screen.py` читает описание из `pub/p/<id>.json` (поле `d`) и ставит `excl` с причиной; карточки с `excl` build скрывает (и PDF, и «Мои Да»). `python3 screen.py --dry` показывает, что отсеется. Если карточка ошибочно отсеяна, поставить `excl_keep: true` в state.json.
- Новые карточки без описания (ещё нет в pack) screen пока не видит: сразу после pack запускать screen и проверять, что в push попадают только прошедшие фильтр (`python3 monitor.py summary` уже их не считает).
- Для Idealista/yaencontre описание берётся из `details/*.json` (fetch в браузере, см. det_i.js/det_y.js), если его нет — вручную прочитать текст объявления перед push.
- Метка сайта `temp` из скриптов Idealista ненадёжна (регэксп ловил «современн»), не использовать как причину отсева.

## Мебель на Fotocasa (исправлено 2026-11-20)
- В ссылке Fotocasa слаг `...-no-amueblado` = БЕЗ мебели. Раньше `enrich.py` принимал его за «с мебелью» (подстрока `amueblado`). Исправлено: `no-amueblado` → `furn: no`, карточка скрывается (`excl`).

## Обновление 2026-11-20 (читать первым)
- **Раздел «За Таррагоной»**: Салоу/Вила-сека, Камбрильс, Реус (группа `G_BEY`). В основных списках не показываются, только в отдельной вкладке. Таррагона, Алтафулья, Торредембарра остаются в группе «Таррагона и побережье».
- **Кнопка «📞 Позвонил»** на каждой карточке + вкладка «📞 Позвонил». Хранится в db-коллекции `marks` полем `c: 1` рядом со статусом `s` (Да/Нет/Смотрел). Позвонившие скрыты из основных списков (видны в «Позвонил» и «Мои Да», если лайкнуты). Колл-во не трогать при публикации.
- **Дома у моря** (вкладка «Дома у моря»): любая жилая недвижимость до 1100 € (chalets, duplex, lofts, aticos, casas) вдоль побережья Барселона-Таррагона и рядом (Барселона, Бахо-Льобрегат, Маресме, Сабадель/Террасса, Гарраф, Таррагона, Алтафулья/Торредембарра, Сант-Кугат, Рубí, Серданьола); ближе за Таррагоной не берём. Сканы: `casas_idealista` (районы + типы), `casas_pisos` (расширен списком побережья), `casas_yae` (+ tarragona-provincia). Ingest: `--casa` (для домов правило FAR выключено).
- **Комнаты Таррагона** (`TGN`): Idealista `/ru/alquiler-habitacion/tarragona-tarragona/`, Pisos `habitaciones-tarragona_capital`, Fotocasa `/es/compartir/pisos/tarragona-capital/...`, Milanuncios `/pisos-compartidos-en-tarragona-tarragona/?hasta=500`. Группа «Таррагона» в разделе «Комнаты». Фильтр «временное/студентам» к комнатам пока не применяется.
- Копирование результатов из вкладки: `LANG=en_US.UTF-8 pbpaste > файл` (иначе кириллица портится).

## Расширение охвата (2026-11-20)
Проверены рабочие адреса (200 OK):
- Habitaclia `/alquiler/viviendas/<slug>/s?minPrice=500&maxPrice=1000&sortType=publicationDate`: l-hospitalet-de-llobregat, cornella-de-llobregat, sant-boi-de-llobregat, rubi, cerdanyola-del-valles, gava, viladecans, sitges, tarragona, reus, el-vendrell, calafell, manresa (salou/reus не показывать: «За Таррагоной»), плюс прежние 9. Делать по ротации: в каждом цикле 9 основных + 4-5 новых по очереди.
- Fotocasa `/es/alquiler/viviendas/<slug>/todas-las-zonas/l?minPrice=500&maxPrice=1000&sortType=publicationDate`: l-hospitalet-de-llobregat, badalona, sabadell, terrassa, tarragona-capital, mataro, sant-cugat-del-valles, cornella-de-llobregat, sant-boi-de-llobregat, sitges, vilanova-i-la-geltru, castelldefels (reus не нужен). Раньше сканировалась только Барселона.
- Milanuncios: у объявлений нет района и адреса (карта), часть из них перепост HousingAnywhere/«no amueblado», размеры «1 м²»: для ingest непригодно. Не использовать, пока не найден способ фильтра «particular».
- Telegram: публичные каналы читаются через `https://t.me/s/<канал>` без входа (нужны названия каналов от пользователя). Instagram: без входа в аккаунт недоступен.
- Spotahome/HousingAnywhere/Uniplaces: в основном среднесрочные/«temporada»: противоречит критерию «не временное», не подключены.

## Описания во всех карточках (2026-11-20, читать)
Причина «Описание не найдено»: в выдаче yaencontre описание обрезано «...», на Idealista/Pisos его не брали. Теперь новый шаг цикла (после ingest/enrich/geo/build/pack, ДО screen.py):
1. `python3 descfill.py direct` (Pisos.com, Fotocasa, Habitaclia напрямую).
2. `python3 descfill.py gen` -> `scan/desc_idea.js` и `scan/desc_yae.js` с адресами карточек без полного описания. Запустить в вкладках Idealista и yaencontre (вставить код через javascript_tool; опрашивать `window.__dd.done`). Результат `window.__dd.out`: положить в `<pre>`, cmd+a, cmd+c, `LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 pbpaste > inbox/desc_idea.json` (и `desc_yae.json`).
3. `python3 descfill.py apply`: вливает в `details/*.json`, помечает снятые (yae 404/410), обновляет поле `d` в `pub/p/*.json`. Потом `screen.py`, build, публикация (в `files` добавить обновлённые `p/*.json`: `find pub/p -newer inbox/desc_yae.json`).
- yae: полное описание в `.box-readmore`; Idealista: `.commentsContainer .comment`. Если у карточки Idealista 404, а описание есть у yaencontre под тем же номером, screen берёт его оттуда.
- screen.py учитывает контекст: «médicos/centros médicos» в перечне «рядом» и «сезонная одежда» не отсеиваются.
- Без описания остаются только карточки, снятые с Idealista, но живые на yae без прямой ссылки (Эшампле 948 €, Террасса 738 €).

## Зона поиска (2026-11-20, обвёл пользователь на карте) и новые полные сканы
Зона: побережье от Матаро через всю Барселону и Бахо-Льобрегат, Гарраф и Баш-Пенедес до Таррагоны + коридор Сабадель/Террасса/Сант-Кугат (Вальес). Внутрь суши дальше Вальеса и Пенедеса не нужно. Раздел «За Таррагоной» (Салоу, Камбрильс, Реус) и Кастельон остаются отдельными вкладками; из Pisos.com Кастельон/Валенсию/Реус/Салоу/Камбрильс в новом скане убрал (в `scan/pisos.js` они остались).
- **Habitaclia и Fotocasa теперь сканируются по сети, не через вкладку-город**: за один запуск ~40 городов зоны (список в самом скрипте), без навигации.
  - `python3 monitor.py scan habitaclia_all` / `fotocasa_all` -> код вставить в вкладку Habitaclia / Fotocasa (`javascript_tool`), опрашивать `window.__sc.done`, `__sc.cities` (сколько карточек нашло в каждом городе), `__sc.out.length`. Habitaclia листается `/s/2`, Fotocasa `/l/2`. Fotocasa отдаёт карточки в JSON страницы (`"detail":{"es-ES":"…/id/d"}`), не в тегах: старый DOM-скрипт видел лишь часть (в этот прогон нашлось ещё ~70 неизвестных).
  - Мебель на Fotocasa: слаг ссылки должен содержать `amueblado` и не `no-amueblado`; иначе пропускаем.
  - Строки забирать через `<pre>` + cmd+a/cmd+c + `pbpaste` (UTF-8), потом `ingest`.
- `scan/pisos.js` расширен ~30 городами зоны (Матаро, Кастельдефельс, Ситжес, Виланова, Кунит, Калафель, Торредембарра, Сант-Бой, В* и т.д.).
- Idealista (комарки Barcelona/ Maresme/ Garraf/ Baix Penedès/ Tarragonès…) и yaencontre (провинции целиком, 89 в Барселоне, 82 в Таррагоне) уже покрывали зону; проверено: Idealista Барселона ≤1000 € всего 76 объявлений, все были просмотрены.
- Старые `scan/habitaclia.js` и `scan/fotocasa.js` (по вкладке) больше не использовать.
