from enum import Enum

class SYMBOL(str,Enum):
    ORO = "XAUUSD"
    BTC = "BTCUSD"
    ETH = "ETHUSD"
    SP500 = "US500.cash"
    NASDAQ = "US100.cash"
    US30 = "US30.cash"
    #LIBRA_USD = "GBPUSD=X"
    #EURO_USD = "EURUSD=X"
    
class SYMBOLS_VLAD(str,Enum):
    ORO = "#ORO"
    XAU = "#XAU"
    BTC = "#BTC"
    BITCOIN = "#BITCOIN"
    ETH = "#ETH"
    SP500 = "#SP500"
    NASDAQ = "#NAS"
    
class SYMBOLS_SNIPERS_GOLD(str,Enum):
    XAU = "XAU"
    XAUUSD = "XAUUSD"
    GOLD = "GOLD"
    BTC = "BTC"
    BITCOIN = "BITCOIN"
    
class PTJG_GOLD(str,Enum):
    ORO = "ORO"
    GOLD = "GOLD"
    XAU = "XAU"
    XAUUSD = "XAUUSD"
    
class TURBO(str,Enum):
    GOLD = "GOLD"
    XAU = "XAU"
    XAUUSD = "XAUUSD"
    BITCOIN = "BITCOIN"
    BTC = "BTC"
    BTC_USD = "BTCUSD"
    
    
    
class US30PRO(str,Enum):
    US30 = "US30"
    
class ENTORNOS(str,Enum):
    DEV = "DEV"
    PRE = "PRE"
    PRO = "PRO"

    

    

