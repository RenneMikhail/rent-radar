# Барселона и окрестности до Таррагоны: муниципалитеты для квартир.
# MUN[zone] = (grade 1-5, note, transport, group)   (оценки по репутации, официальных данных по каждому городу здесь нет)
G_BCN = "Барселона"
G_BAIX = "Бахо-Льобрегат и Барселонес"
G_MAR = "Маресме"
G_VAL = "Вальес"
G_ST = "Сабадель и Террасса"
G_GAR = "Гарраф и Пенедес"
G_TAR = "Таррагона и побережье"
G_BEY = "За Таррагоной"
G_HR = "В часе от Барселоны"
M = lambda g, n, t, grp: (g, n, t, [], "репутация (по общим знаниям, без источника)", grp)
MUN = {
 "Manresa": M(3, "Областной центр Бages, 1 час на поезде/машине, спокойный.", "Rodalies R5/R4, FGC, автобус ~1 ч", G_HR),
 "Igualada": M(3, "Город в Анойе, спокойный, ~1 ч на автобусе.", "Автобус/Rodalies R6 ~1 ч", G_HR),
 "Vic": M(4, "Университетский город в Осоне, спокойный.", "Rodalies R3 ~1 ч", G_HR),
 "Blanes/Tordera": M(3, "Прибрежный город на границе Жироны, ~1 ч поездом.", "Rodalies R1 ~1 ч", G_HR),
 "L'Hospitalet (Santa Eulàlia/Bellvitge)": M(3, "Плотная застройка рядом с Барселоной, жильё дешевле; район спокойный, но шумный.", "Метро L1/L5/L9, Rodalies", G_BAIX),
 "L'Hospitalet (Collblanc/La Torrassa)": M(2, "Низкие доходы, много жалоб на безопасность и точки торговли.", "Метро L5/L9", G_BAIX),
 "Esplugues de Llobregat": M(4, "Тихий жилой пригород у Diagonal, парки.", "Трамвай T1/T2/T3, метро L3 рядом, автобусы", G_BAIX),
 "Sant Just Desvern": M(5, "Спокойный, зелёный, высокие цены; один из лучших пригородов.", "Трамвай, FGC, автобусы до Диагональ", G_BAIX),
 "Sant Joan Despí": M(4, "Жилой, спокойный, есть река и парки.", "Трамвай T1/T2/T3, Rodalies/FGC", G_BAIX),
 "Cornellà de Llobregat": M(3, "Рабочий пригород, смешанный; ближе к Барселоне чище.", "Метро L5, трамвай, Rodalies", G_BAIX),
 "Sant Feliu/Molins de Rei": M(4, "Небольшие города с историческим центром, спокойно.", "FGC S33/Rodalies R4", G_BAIX),
 "Viladecans/Gavà": M(3, "Жилые города у моря, рядом аэропорт (шум самолётов).", "Rodalies R2, автобусы", G_BAIX),
 "Castelldefels": M(4, "Пляж, жилые районы, летом много людей.", "Rodalies R2 Sud", G_BAIX),
 "El Prat de Llobregat": M(3, "Рядом аэропорт: шум самолётов, промзона.", "Метро L9, Rodalies R2", G_BAIX),
 "Badalona (центр/Pomar/Gorg)": M(3, "Большой город, смешанный; ближе к морю лучше.", "Метро L2/L4, Rodalies R1", G_MAR),
 "Badalona (Sant Roc/La Pau/Llefià)": M(2, "Проблемные кварталы: торговля наркотиками, низкие доходы.", "Метро L10", G_MAR),
 "Santa Coloma de Gramenet": M(2, "Плотная застройка, низкие доходы, проблемные кварталы (Singuerlín, Fondo).", "Метро L1/L9", G_BAIX),
 "Sant Adrià de Besòs": M(2, "Промзоны и район La Mina с наркоторговлей.", "Метро L4, трамвай", G_BAIX),
 "Montgat/Tiana/Teià": M(4, "Небольшие тихие города у моря.", "Rodalies R1", G_MAR),
 "El Masnou/Premià de Mar/Vilassar": M(4, "Жилые прибрежные города, пляж и поезд.", "Rodalies R1", G_MAR),
 "Mataró": M(3, "Крупный город, центр и пляж спокойные, окраины смешанные.", "Rodalies R1", G_MAR),
 "Sant Cugat del Vallès": M(5, "Зажиточный, зелёный, очень безопасный.", "FGC S1/S2, Rodalies", G_VAL),
 "Cerdanyola/Ripollet/Montcada": M(3, "Университет UAB в Cerdanyola, остальное смешанное.", "Rodalies R4/R7, FGC", G_VAL),
 "Sabadell": M(3, "Крупный промышленный город, есть спокойные зоны.", "Rodalies R4, FGC S2 (электрички в Барселону)", G_ST),
 "Terrassa": M(3, "Крупный город, смешанный.", "FGC S1, Rodalies R4 (электрички в Барселону)", G_ST),
 "Rubí": M(3, "Жилой, средний.", "FGC S5/S55, Rodalies", G_VAL),
 "Granollers": M(3, "Спокойный городок вне агломерации.", "Rodalies R2/R3", G_VAL),
 "Sitges": M(4, "Курорт, красивый, но дорогой и туристический.", "Rodalies R2 Sud", G_GAR),
 "Vilanova i la Geltrú": M(3, "Прибрежный город, спокойный.", "Rodalies R2 Sud", G_GAR),
 "Vilafranca del Penedès": M(3, "Небольшой город в винной зоне.", "Rodalies R4", G_GAR),
 "Calafell/Cunit/Segur": M(3, "Летние пляжные посёлки, зимой пусто.", "Rodalies R2 Sud", G_GAR),
 "Tarragona (центр/Part Alta)": M(4, "Исторический центр и пляж, спокойно.", "Rodalies R14/R16, AVE Camp de Tarragona", G_TAR),
 "Tarragona (Torreforta/Bonavista/Campclar)": M(2, "Социально сложные кварталы и рядом нефтехимическая промзона.", "Автобусы", G_TAR),
 "Reus": M(3, "Крупный город, центр хороший, окраины смешанные.", "Rodalies R14, рядом аэропорт", G_BEY),
 "Salou/Vila-seca": M(3, "Туристический курорт, зимой тихо; рядом нефтехимия Tarragona.", "Rodalies R16", G_BEY),
 "Cambrils": M(4, "Спокойный прибрежный город, за Таррагоной.", "Rodalies R16", G_BEY),
 "Altafulla/Torredembarra": M(4, "Спокойные прибрежные города между Таррагоной и Барселоной.", "Rodalies R2 Sud", G_TAR),
 "Tarragona общий": M(3, "Район в объявлении не указан.", "Rodalies R14/R16", G_TAR),
}
MUN_RULES = [
 (r"sant iscle de vallalta|argentona|cabrils|vilassar de dalt|premi[aà] de dalt|llavaneres|sant vicen[cç] de montalt|caldes d.estrac|sant andreu de llavaneres|orrius|[oò]rrius|dosrius|sant cebri", "Mataró"),
 (r"sant quirze del vall|barber[aà] del vall|castellar del vall|polinya|palau.?solit|sentmenat|matadepera|viladecavalls|ullastrell|badia del vall|gallifa", "Terrassa"),
 (r"castellbisbal|la palma de cervell|cervell[oó]|sant climent de llobregat|begues|torrelles de llobregat|santa coloma de cervell|sant esteve sesrovires|corbera de llobregat", "Sant Feliu/Molins de Rei"),
 (r"manresa|sant fruit[oó]s de bages|navarcles", "Manresa"), (r"igualada|[oó]dena|[ií]gualada", "Igualada"), (r"\bvic\b|manlleu|torell[oó]", "Vic"), (r"blanes|tordera", "Blanes/Tordera"),
 (r"hospitalet de l.infant|vandell|mont.?roig|miami platja|alcanar|ampolla|ametlla|sant carles de la r|tortosa|flix|deltebre|sant jaume d.enveja|tivenys|ulldecona|vinaroz|vinar", None),
 (r"matar[oó]", "Mataró"),
 (r"0820[1-8]", "Sabadell"), (r"0822[1-9]", "Terrassa"),
 (r"esparreguera|sant andreu de la barca|sant vicen[cç] dels horts|pallej[aà]|martorell|abrera|olesa|cervell", "Sant Feliu/Molins de Rei"),
 (r"sant cebri[aà] de vallalta|pineda de mar|calella|arenys|canet de mar|malgrat|sant pol de mar|santa susanna|vilassar|cabrera de mar|alella|teia|premi", "El Masnou/Premià de Mar/Vilassar"),
 (r"vilafortuny|cap de sant pere|el maset", "Cambrils"), (r"roda de ber|creixell|coma.?ruga|el vendrell", "Altafulla/Torredembarra"),
 (r"collblanc|torrassa|la torrassa", "L'Hospitalet (Collblanc/La Torrassa)"),
 (r"hospitalet|оспиталет", "L'Hospitalet (Santa Eulàlia/Bellvitge)"),
 (r"esplugues|эспльюгес", "Esplugues de Llobregat"), (r"sant just desvern|сан-?жуст|сант-?жуст", "Sant Just Desvern"),
 (r"sant joan desp|сант-?жоан-?десп|сан-?хоан-?десп", "Sant Joan Despí"),
 (r"cornell[aà]|корнелья", "Cornellà de Llobregat"),
 (r"sant feliu de llobregat|molins de rei|сант-?фелиу|молинс", "Sant Feliu/Molins de Rei"),
 (r"viladecans|gav[aà]\b|вильядекан|гава\b", "Viladecans/Gavà"), (r"castelldefels|кастельдефельс", "Castelldefels"),
 (r"el prat de llobregat|\bel prat\b|эль-?прат", "El Prat de Llobregat"),
 (r"sant roc|la pau|llefi[aà]|ллефия", "Badalona (Sant Roc/La Pau/Llefià)"), (r"badalona|бадалон", "Badalona (центр/Pomar/Gorg)"),
 (r"santa coloma|санта-?колом", "Santa Coloma de Gramenet"), (r"sant adri[aà]|сант-?адри|сан-?адри", "Sant Adrià de Besòs"),
 (r"montgat|tiana|te[ií]a|монтгат|тиана", "Montgat/Tiana/Teià"),
 (r"masnou|premi[aà]|vilassar|масноу|премия|вилассар", "El Masnou/Premià de Mar/Vilassar"), (r"matar[oó]|матаро", "Mataró"),
 (r"sant cugat|сан-?кугат|сант-?кугат", "Sant Cugat del Vallès"), (r"cerdanyola|ripollet|montcada i reixac|сердань|рипольет", "Cerdanyola/Ripollet/Montcada"),
 (r"sabadell|сабадель", "Sabadell"), (r"terrassa|\bтеррас[аеу]?\b(?!\w)(?<!с террас)|терраса,", "Terrassa"), (r"\brub[ií]\b|руби\b", "Rubí"), (r"granollers|la garriga|mollet del vall|santa eul[aà]lia de ron|гранольерс", "Granollers"),
 (r"sitges|ситжес", "Sitges"), (r"cubelles|sant pere de ribes|sant pere de ribes", "Vilanova i la Geltrú"), (r"vilanova i la geltr|vilanova i la geltru|вилланова|виланова", "Vilanova i la Geltrú"), (r"santa margarida i els monjos|sant sadurn[ií]|torrelles de foix|vilafranca|вилафранка", "Vilafranca del Penedès"),
 (r"calafell|cunit|segur de calafell|калафель|кунит", "Calafell/Cunit/Segur"),
 (r"cambrils|capellans|камбрильс", "Cambrils"), (r"altafulla|torredembarra|альтафулья|торредембарра", "Altafulla/Torredembarra"),
 (r"\breus\b|реус", "Reus"), (r"salou|vila.?seca|la pineda|салоу|вила-?сека", "Salou/Vila-seca"),
 (r"torreforta|bonavista|campclar|ponent", "Tarragona (Torreforta/Bonavista/Campclar)"),
 (r"tarragona|таррагон", "Tarragona (центр/Part Alta)"),]
