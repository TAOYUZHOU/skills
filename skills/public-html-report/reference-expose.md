# Expose reference (nginx + SG)

## nginx

`/etc/nginx/sites-available/public-html-report`:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:18765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

```bash
sudo ln -sfn /etc/nginx/sites-available/public-html-report /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl enable --now nginx && sudo systemctl reload nginx
```

Change `18765` to the local auth server port.

## Security group

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXX \
  --protocol tcp --port 80 \
  --cidr 203.0.113.0/24   # prefer team CIDR over 0.0.0.0/0
```

## Verify

```bash
PUBLIC_IP=$(curl -s ifconfig.me)
curl -s -o /dev/null -w '%{http_code}\n' -u 'USER:PASS' "http://${PUBLIC_IP}/"
```

## PUBLIC_URL.txt template

```
Report: <title>
URL:    http://<PUBLIC_IP>/
Auth:   <user> / (password out-of-band)
Backend: nginx :80 → 127.0.0.1:<PORT>
```

## AutoDL alternate (no fixed team IP)

When the host is AutoDL (or similar) and nginx + public IP is unavailable, use skill
**`static-html-report-serve`** (自定义服务 port **6006**, `AutoDLService6006URL`).

```bash
SKILL=/root/autodl-tmp/taoyuzhou/skills/skills/static-html-report-serve
"$SKILL/scripts/serve_html_report.sh" \
  --dir /path/to/publish_tree \
  --entry index.html
```

**Tradeoffs (read before sharing):**

- Typically **no HTTP Basic Auth** — anyone with the URL can read everything under `--dir`
- Prefer a minimal `publish/` tree (HTML + needed assets only); never serve repo root
- URL dies when the instance stops or is rebuilt; restart serve after reboot
- Full risk table and Feishu notes live in that skill's `SKILL.md`

Prefer the nginx + Basic Auth path above whenever a day-stable fixed IP is available.