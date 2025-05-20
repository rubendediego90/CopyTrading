from enum import Enum

    
class CONFIG_NAME_STRATEGY(str,Enum):
    PTJG_GOLD_PUB = "PTGP"
    SNIPERS_GOLD_VIP = "SPGV"
    SNIPERS_GOLD_PUB = "SPGP"
    VLAD = "VLAD"
    US30_PRO = "U30P"
    TURBO_PUBLIC = "TURP"
    
class CONFIG_STRATEGY_PROPERTIES(str,Enum):
    RISK = "riesgo"
    AUTO_SL = "auto_stop_loss"
    TP_AUTO_SL = "tp"
    CLOSE_PENDIGNS_IN_NEW = "close_pendings_in_new"
    CLOSE_OPENS_IN_NEW = "close_opens_in_new"
    
    

