from pathlib import Path


class RedisConf:
    def __init__(self):
        self.dir = Path.cwd() / "redis-data"
        self.dbfile = self.dir / "rdbfile"
        self._default()

    def _default(self) -> None:
        self.dir.mkdir(exist_ok=True)
        self.dbfile.touch(exist_ok=True)
