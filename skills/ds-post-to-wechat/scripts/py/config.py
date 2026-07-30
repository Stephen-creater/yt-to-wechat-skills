#!/usr/bin/env python3
"""
配置加载 — 与 TS 脚本共享 .ds-skills/ 配置体系。

凭证查找顺序：
  1. 环境变量 WECHAT_APP_ID / WECHAT_APP_SECRET
  2. <cwd>/.ds-skills/.env
  3. ~/.ds-skills/.env

EXTEND.md 查找顺序（用于 remote_publish_* 等键）：
  1. <cwd>/.ds-skills/ds-post-to-wechat/EXTEND.md
  2. ${XDG_CONFIG_HOME:-~/.config}/ds-skills/ds-post-to-wechat/EXTEND.md
  3. ~/.ds-skills/ds-post-to-wechat/EXTEND.md
"""

import os
from pathlib import Path


def _parse_kv_file(path: Path) -> dict:
    """通用 KEY: value 或 KEY=value 解析"""
    result = {}
    if not path.exists():
        return result
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line and not line.startswith('='):
                key, _, value = line.partition(':')
            elif '=' in line:
                key, _, value = line.partition('=')
            else:
                continue
            # strip inline comments
            value = value.split('#', 1)[0]
            result[key.strip()] = value.strip()
    return result


def _env_search_paths() -> list:
    return [
        Path.cwd() / '.ds-skills' / '.env',
        Path.home() / '.ds-skills' / '.env',
    ]


def _extend_search_paths() -> list:
    xdg = os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
    return [
        Path.cwd() / '.ds-skills' / 'ds-post-to-wechat' / 'EXTEND.md',
        Path(xdg) / 'ds-skills' / 'ds-post-to-wechat' / 'EXTEND.md',
        Path.home() / '.ds-skills' / 'ds-post-to-wechat' / 'EXTEND.md',
    ]


def load_env() -> dict:
    """合并所有 .env 文件，cwd 优先"""
    merged = {}
    for p in reversed(_env_search_paths()):  # later overrides earlier; cwd last → wins
        merged.update(_parse_kv_file(p))
    return merged


def load_extend() -> dict:
    """读取第一个命中的 EXTEND.md"""
    for p in _extend_search_paths():
        if p.exists():
            return _parse_kv_file(p)
    return {}


def get_wechat_config() -> dict:
    """返回 app_id / app_secret，环境变量优先于 .env"""
    env_file = load_env()
    return {
        'app_id': os.environ.get('WECHAT_APP_ID') or env_file.get('WECHAT_APP_ID', ''),
        'app_secret': os.environ.get('WECHAT_APP_SECRET') or env_file.get('WECHAT_APP_SECRET', ''),
    }


def get_remote_config() -> dict:
    """从 EXTEND.md 读取 remote_publish_* 键"""
    extend = load_extend()

    def _bool(key: str, default: bool = False) -> bool:
        v = extend.get(key)
        if v is None:
            return default
        return str(v).lower() in ('1', 'true', 'yes', 'on')

    method = extend.get('default_publish_method', '').strip().lower()

    return {
        'enabled': method == 'remote-api',
        'host': extend.get('remote_publish_host'),
        'user': extend.get('remote_publish_user', 'root'),
        'port': int(extend.get('remote_publish_port', '22') or 22),
        'identity_file': extend.get('remote_publish_identity_file'),
        'known_hosts_file': extend.get('remote_publish_known_hosts_file'),
        'strict_host_key_checking': extend.get('remote_publish_strict_host_key_checking', 'accept-new'),
        'connect_timeout': int(extend.get('remote_publish_connect_timeout', '10') or 10),
        'proxy_jump': extend.get('remote_publish_proxy_jump'),
    }


if __name__ == '__main__':
    wechat = get_wechat_config()
    remote = get_remote_config()
    print(f"AppID: {wechat['app_id']}")
    print(f"AppSecret: {wechat['app_secret'][:10]}..." if wechat['app_secret'] else "AppSecret: (未配置)")
    print(f"Remote enabled: {remote['enabled']}")
    if remote['host']:
        print(f"Remote: {remote['user']}@{remote['host']}:{remote['port']} ({remote['identity_file']})")
