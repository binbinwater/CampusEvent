# 部署参考

公网演示使用 Ubuntu 24.04 + Nginx + Gunicorn，应用挂在 `/campusevent/` 前缀。

1. 将项目上传到 `/opt/campusevent`，创建无登录系统用户 `campusevent`。
2. 创建虚拟环境并安装依赖：

```bash
python3 -m venv /opt/campusevent/.venv
/opt/campusevent/.venv/bin/pip install -r /opt/campusevent/requirements-deploy.txt
sudo -u campusevent sh -c 'cd /opt/campusevent && .venv/bin/python -m flask --app run.py init-db'
```

3. 将 `campusevent.service` 安装到 `/etc/systemd/system/`，把 `CAMPUSEVENT_SECRET_KEY` 替换为随机值，然后 `systemctl daemon-reload && systemctl enable --now campusevent`。
4. 将 `nginx-location.conf` 合并进 80 端口站点，并确保前缀请求原样转发（`proxy_pass http://127.0.0.1:8001;` 末尾不能加 `/`）。`wsgi.py` 的 `DispatcherMiddleware` 会设置 `SCRIPT_NAME=/campusevent`。
5. `nginx -t && systemctl reload nginx`。
6. 验证 `/campusevent/login`、静态文件和登录后的页面。

`.deploy/`、密码、随机 SECRET_KEY 和数据库不进入版本库。公网演示使用固定演示账号，需配合访问控制，不能作为生产部署。