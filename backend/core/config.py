from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    APP_HOST: str
    APP_PORT: int

    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: SecretStr
    MYSQL_DB: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: SecretStr

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int

    RATE_LIMIT_PER_MINUTE: int
    WS_HEARTBEAT_TIMEOUT_SECONDS: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def mysql_password(self) -> str:
        return self.MYSQL_PASSWORD.get_secret_value()

    @property
    def redis_password(self) -> str:
        return self.REDIS_PASSWORD.get_secret_value()

    @property
    def jwt_secret_key(self) -> str:
        return self.JWT_SECRET_KEY.get_secret_value()
#这三个函数作用是为了安全地获取敏感信息（如数据库密码、Redis密码和JWT密钥）。它们使用Pydantic的SecretStr类型来存储这些敏感信息，并通过get_secret_value()方法来获取实际的字符串值。这种方式可以防止在日志或错误消息中意外泄露敏感信息，同时仍然允许应用程序安全地访问这些值。
#get_secret_value()从哪里获取值？它从Settings类的属性中获取值，这些属性是通过环境变量或.env文件加载的。当应用程序运行时，Pydantic会自动读取这些配置值，并将它们存储在Settings对象中。通过调用这些属性的get_secret_value()方法，应用程序可以安全地访问这些敏感信息，而不会直接暴露它们的值。

settings = Settings() #settings对象是Settings类的一个实例，它会自动从环境变量或.env文件中加载配置值。通过访问settings对象的属性，应用程序可以获取所需的配置参数，例如数据库连接信息、JWT密钥等。这种集中管理配置的方式使得应用程序更易于维护和部署。
