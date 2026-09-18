"""Rosters fixos - BINGO (9 contas no FINAL) e REALS (53 contas)."""

# BTAG, USERNAME, entra_no_BEKAS
BINGO = [
    ("38579", "Bigthiago00", True),
    ("38541", "Bigthiago01", True),
    ("38606", "Bigthiago02", True),
    ("39705", "Bigthiago05 - PABLO", True),
    ("38438", "Bigthiago11", True),
    ("38614", "Nikolas00", True),
    ("39685", "Nikolas001", True),
    ("40271", "Instahacker", True),
    ("41735", "TheuDados", False),   # FINAL sim, FORA do BEKAS
]

EXCLUIDOS = {"41738"}  # wesley01 - excluido sempre, toda plataforma

REVSHARE35_REALS = {"25945", "10020", "21679"}  # Danielribas, Danielribas11, Danielribas2002

REALS = [
    ("25945", "Danielribas"), ("10020", "Danielribas11"), ("21679", "Danielribas2002"),
    ("25942", "100jeito"), ("25955", "Nikolas46"), ("26390", "Yasminofc"),
    ("26277", "Vikevitoria01"), ("26562", "Vanessafreitas"), ("21683", "Vagner01"),
    ("26547", "Shaycosta"), ("21751", "Ruth01"), ("25986", "Rodigo_liso"),
    ("10222", "Raymarcelle01"), ("26512", "rarykasousa"), ("26774", "raiane.pereira"),
    ("26298", "Ptwillames"), ("21775", "pre_13"), ("26138", "Peuzinho"),
    ("36275", "pererafany01"), ("21773", "nathcrazy"), ("26559", "Nargiane"),
    ("21675", "Millyfefe"), ("10085", "Mayra01"), ("25937", "Livia01"),
    ("32562", "Larissarozendo"), ("10234", "Kayk01"), ("26582", "Kamila96"),
    ("26320", "Juliaalvarengaa"), ("26586", "josielson"), ("26469", "Jenniferkareen_"),
    ("10079", "japona"), ("10084", "Indiera1993"), ("10172", "Ianka01"),
    ("10052", "Giovannamazzali"), ("26600", "Felipefontenele"), ("32219", "Eveline01"),
    ("26765", "Eupeioxoto"), ("26474", "Emillyee"), ("32584", "danivieiraofc"),
    ("26567", "Claudenia"), ("26528", "Chicomson"), ("26462", "CecyLimaaa"),
    ("26675", "camillamoraes2023"), ("26441", "Brenoo"), ("21757", "Braidscinthia"),
    ("26502", "beeca91"), ("26569", "amanda123"), ("10258", "Alinerodrigues"),
    ("26142", "acerolaof"), ("21693", "Abner01"), ("21698", "100jeito01"),
    ("26153", "wallysson.11"), ("26299", "iggor_ofc"),
]

OBS = {
    "41735": "FINAL sim / FORA do BEKAS",
    "21757": "ausente do export REALS -> 0/0",
    "10020": "alta volatilidade - conferir",
}

assert len(BINGO) == 9, len(BINGO)
assert len(REALS) == 53, len(REALS)
