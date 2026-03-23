import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PRIVATE_KEY: str                 = os.getenv("PRIVATE_KEY", "")
    OPENAI_API_KEY: str              = os.getenv("OPENAI_API_KEY", "")
    PINATA_JWT: str                  = os.getenv("PINATA_JWT", "")
    NFT_STORAGE_API_KEY: str         = os.getenv("NFT_STORAGE_API_KEY", "")
    SOLANA_RPC_URL: str              = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    PUMPPORTAL_API_KEY: str          = os.getenv("PUMPPORTAL_API_KEY", "")
    USE_PUMPFUN_IPFS: bool           = os.getenv("USE_PUMPFUN_IPFS", "false").lower() == "true"
    DEFAULT_SLIPPAGE: int            = int(os.getenv("DEFAULT_SLIPPAGE", "10"))
    DEFAULT_PRIORITY_FEE: float      = float(os.getenv("DEFAULT_PRIORITY_FEE", "0.0005"))
    DEFAULT_INITIAL_BUY_SOL: float   = float(os.getenv("DEFAULT_INITIAL_BUY_SOL", "0"))
    IMAGE_STYLE: str                 = os.getenv("IMAGE_STYLE", "vibrant")
    OUTPUT_DIR: str                  = os.getenv("OUTPUT_DIR", "./output")
    LOG_LEVEL: str                   = os.getenv("LOG_LEVEL", "INFO")

    PUMPFUN_IPFS_URL    = "https://pump.fun/api/ipfs"
    PUMPPORTAL_API_URL  = "https://pumpportal.fun/api"
    PINATA_UPLOAD_URL   = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    PINATA_JSON_URL     = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    PINATA_GATEWAY      = "https://gateway.pinata.cloud/ipfs"
    NFT_STORAGE_URL     = "https://api.nft.storage/upload"
    SOLANA_EXPLORER     = "https://explorer.solana.com"
    DEXSCREENER_URL     = "https://dexscreener.com/solana"
    PUMPFUN_URL         = "https://pump.fun"

    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    def has_pinata(self) -> bool:
        return bool(self.PINATA_JWT)

    def has_wallet(self) -> bool:
        return bool(self.PRIVATE_KEY)

config = Config()
