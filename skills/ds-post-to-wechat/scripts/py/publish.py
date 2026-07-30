#!/usr/bin/env python3
"""
发布小绿书（贴图号 / newspic）到微信公众号草稿箱。

支持 SSH SOCKS5 隧道（与 ds-post-to-wechat 的文章发布共用同一套 EXTEND.md
remote_publish_* 配置）。当 EXTEND.md 中 default_publish_method=remote-api
或显式传 --remote 时，所有微信 API 调用走 ssh -N -D 起的本地 SOCKS5。

使用：
    # 纯文字（自动用占位图）
    python3 publish.py --title "标题" --content "正文"

    # 带永久素材 media_id
    python3 publish.py --title "标题" --content "正文" --images "ID1,ID2"

    # 带本地图片（自动上传永久素材）
    python3 publish.py --title "标题" --content_file article.txt --image_files "1.jpg,2.jpg"

    # 显式走远程隧道
    python3 publish.py --title "标题" --content "正文" --remote
"""

import argparse
import contextlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests


# ----------------------------- SSH SOCKS5 tunnel ----------------------------- #

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _wait_socks_ready(port: int, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1.0):
                return
        except OSError as e:
            last_err = e
            time.sleep(0.1)
    raise RuntimeError(f"SOCKS proxy on 127.0.0.1:{port} not ready within {timeout_s}s: {last_err}")


def _build_ssh_args(remote: dict, socks_port: int) -> list:
    args = [
        'ssh', '-N',
        '-D', f'127.0.0.1:{socks_port}',
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'ServerAliveInterval=30',
        '-o', f"StrictHostKeyChecking={remote.get('strict_host_key_checking', 'accept-new')}",
        '-o', f"ConnectTimeout={remote.get('connect_timeout', 10)}",
        '-p', str(remote.get('port', 22)),
    ]
    if remote.get('identity_file'):
        identity = os.path.expanduser(remote['identity_file'])
        args += ['-i', identity, '-o', 'IdentitiesOnly=yes']
    if remote.get('known_hosts_file'):
        args += ['-o', f"UserKnownHostsFile={os.path.expanduser(remote['known_hosts_file'])}"]
    if remote.get('proxy_jump'):
        args += ['-J', remote['proxy_jump']]
    args += [f"{remote.get('user', 'root')}@{remote['host']}"]
    return args


@contextlib.contextmanager
def ssh_tunnel(remote: dict):
    """Context manager: 启动 ssh -N -D，yield proxies dict，退出时关闭隧道。"""
    if not remote.get('host'):
        raise RuntimeError("Remote publish host is required (set remote_publish_host in EXTEND.md or --remote-host)")
    port = _find_free_port()
    cmd = _build_ssh_args(remote, port)
    print(f"[ssh-tunnel] starting: {' '.join(cmd)}", file=sys.stderr)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        try:
            _wait_socks_ready(port)
        except Exception:
            # If ssh exited early, surface its stderr
            try:
                _, err = proc.communicate(timeout=0.5)
            except subprocess.TimeoutExpired:
                err = b''
            if err:
                sys.stderr.write(err.decode('utf-8', 'replace'))
            raise
        proxies = {
            'http': f'socks5h://127.0.0.1:{port}',
            'https': f'socks5h://127.0.0.1:{port}',
        }
        yield proxies
    finally:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            pass


# ---------------------------- WeChat API helpers ---------------------------- #

def get_access_token(app_id, app_secret, proxies=None):
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
    r = requests.get(url, params=params, timeout=30, proxies=proxies)
    if r.status_code >= 400:
        raise Exception(f"HTTP {r.status_code}: {r.text}")
    data = r.json()
    if data.get("errcode", 0) != 0:
        raise Exception(f"微信错误[{data['errcode']}] {data.get('errmsg', '未知')}")
    if not data.get("access_token"):
        raise Exception("响应中未找到 access_token")
    return data["access_token"]


def upload_image(access_token, image_path, proxies=None):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(image_path, 'rb') as f:
        r = requests.post(url, files={'media': f}, timeout=60, proxies=proxies)
    data = r.json()
    if 'media_id' not in data:
        raise Exception(f"上传图片失败: [{data.get('errcode', '?')}] {data.get('errmsg', '未知')}")
    return data['media_id']


def create_draft(access_token, title, content, image_media_ids, proxies=None):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    article = {
        "article_type": "newspic",
        "title": title,
        "content": content,
        "image_info": {"image_list": [{"image_media_id": mid} for mid in image_media_ids]},
    }
    body = json.dumps({"articles": [article]}, ensure_ascii=False).encode('utf-8')
    r = requests.post(url, data=body,
                      headers={"Content-Type": "application/json; charset=utf-8"},
                      timeout=30, proxies=proxies)
    if r.status_code >= 400:
        raise Exception(f"HTTP {r.status_code}: {r.text}")
    data = r.json()
    if data.get("errcode", 0) != 0:
        hints = {40001: "access_token 无效/过期", 40007: "无效 media_id",
                 45001: "文件超限", 40125: "无效 AppID/Secret",
                 40164: "IP 不在白名单（公众号 → 开发 → IP白名单）"}
        hint = hints.get(data['errcode'], '')
        raise Exception(f"微信错误[{data['errcode']}] {data.get('errmsg', '未知')}" + (f" ({hint})" if hint else ""))
    if not data.get("media_id"):
        raise Exception("未获取到 media_id")
    return data["media_id"]


# ------------------------------------ main ----------------------------------- #

def _resolve_placeholder():
    here = Path(__file__).resolve().parent
    return here.parent.parent / 'placeholder.jpg'  # scripts/py/.. /.. = skill root


def main():
    p = argparse.ArgumentParser(description="发布小绿书到微信公众号草稿箱")
    p.add_argument("--title", required=True, help="标题（最多 20 字）")
    p.add_argument("--content", default=None)
    p.add_argument("--content_file", default=None)
    p.add_argument("--images", default=None, help="永久素材 media_id 列表，逗号分隔")
    p.add_argument("--image_files", default=None, help="本地图片路径，逗号分隔（自动上传）")
    p.add_argument("--app_id", help="覆盖 .env 中的 WECHAT_APP_ID")
    p.add_argument("--app_secret", help="覆盖 .env 中的 WECHAT_APP_SECRET")
    p.add_argument("--remote", action="store_true", help="走 SSH SOCKS5 隧道（默认读 EXTEND.md）")
    p.add_argument("--no-remote", action="store_true", help="强制本地直连，覆盖 EXTEND.md")
    p.add_argument("--remote-host"); p.add_argument("--remote-user")
    p.add_argument("--remote-port", type=int); p.add_argument("--remote-identity-file")
    p.add_argument("--remote-known-hosts-file"); p.add_argument("--remote-proxy-jump")
    p.add_argument("--remote-connect-timeout", type=int)
    p.add_argument("--remote-strict-host-key-checking",
                   choices=['yes', 'no', 'accept-new'])
    args = p.parse_args()

    # content
    content = args.content
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    if not content:
        sys.exit("错误: 需要 --content 或 --content_file")

    # credentials
    try:
        from config import get_wechat_config, get_remote_config
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from config import get_wechat_config, get_remote_config
    cred = get_wechat_config()
    app_id = args.app_id or cred['app_id']
    app_secret = args.app_secret or cred['app_secret']
    if not app_id or not app_secret:
        sys.exit("错误: 缺少 WECHAT_APP_ID / WECHAT_APP_SECRET（设 .ds-skills/.env 或传 --app_id/--app_secret）")

    # remote config: CLI > EXTEND.md
    remote_cfg = get_remote_config()
    use_remote = (remote_cfg['enabled'] or args.remote) and not args.no_remote
    # CLI override
    if args.remote_host: remote_cfg['host'] = args.remote_host; use_remote = True
    if args.remote_user: remote_cfg['user'] = args.remote_user
    if args.remote_port: remote_cfg['port'] = args.remote_port
    if args.remote_identity_file: remote_cfg['identity_file'] = args.remote_identity_file
    if args.remote_known_hosts_file: remote_cfg['known_hosts_file'] = args.remote_known_hosts_file
    if args.remote_proxy_jump: remote_cfg['proxy_jump'] = args.remote_proxy_jump
    if args.remote_connect_timeout: remote_cfg['connect_timeout'] = args.remote_connect_timeout
    if args.remote_strict_host_key_checking:
        remote_cfg['strict_host_key_checking'] = args.remote_strict_host_key_checking

    # tunnel context (no-op if not remote)
    @contextlib.contextmanager
    def _maybe_tunnel():
        if use_remote:
            with ssh_tunnel(remote_cfg) as proxies:
                yield proxies
        else:
            yield None

    try:
        with _maybe_tunnel() as proxies:
            token = get_access_token(app_id, app_secret, proxies=proxies)

            # image collection
            image_ids = []
            if args.images:
                image_ids += [m.strip() for m in args.images.split(',') if m.strip()]
            if args.image_files:
                for path in args.image_files.split(','):
                    path = path.strip()
                    if not path:
                        continue
                    print(f"[upload] {path}", file=sys.stderr)
                    image_ids.append(upload_image(token, path, proxies=proxies))

            if not image_ids:
                placeholder = _resolve_placeholder()
                if not placeholder.exists():
                    raise FileNotFoundError(f"占位图缺失: {placeholder}")
                print("[upload] placeholder.jpg (newspic 至少需要一张图)", file=sys.stderr)
                image_ids.append(upload_image(token, str(placeholder), proxies=proxies))

            media_id = create_draft(token, args.title, content, image_ids, proxies=proxies)
            print(json.dumps({
                "status": "success",
                "media_id": media_id,
                "via": "remote-api" if use_remote else "api",
                "image_count": len(image_ids),
            }, ensure_ascii=False, indent=2))
    except Exception as e:
        sys.exit(f"错误: {e}")


if __name__ == "__main__":
    main()
