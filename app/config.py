from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    sendblue_apiurl: str
    sendblue_apikey: str
    sendblue_apisecret: str
    langchain_api_key: str
    openai_api_key: str

    model_config = SettingsConfigDict(env_file=".env")
