from enum import Enum

    
class CONFIG_NAME_STRATEGY(str,Enum):
    PTJG_GOLD_PUB = "PTGP"
    SNIPERS_GOLD_VIP = "SPGV"
    JOAN_GOLD_VIP = "JOAN"
    SNIPERS_GOLD_PUB = "SPGP"
    VLAD = "VLAD"
    NASDAQ_100 = "N100"
    TURBO_PUBLIC = "TURP"
    
class CONFIG_STRATEGY_PROPERTIES(str,Enum):
    RISK = "riesgo"
    TP_AUTO_SL = "tp"
    CLOSE_PENDIGNS_IN_NEW = "close_pendings_in_new"
    CLOSE_OPENS_IN_NEW = "close_opens_in_new"
    
    

