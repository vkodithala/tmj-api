from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    sendblue_apiurl: str
    sendblue_apikey: str
    sendblue_apisecret: str

    model_config = SettingsConfigDict(env_file=".env")
