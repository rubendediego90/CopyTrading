from enum import Enum

class CONFIG_COMMENT(str,Enum):
    AUTO_SL = "_ASL"
    
class CONFIG_NAME_STRATEGY(str,Enum):
    PTJG_GOLD_PUB = "PTGP"
    SNIPERS_GOLD_VIP = "SPGV"
    SNIPERS_GOLD_PUB = "SPGP"
    VLAD = "VLAD"
    US30_PRO = "U30P"

    

