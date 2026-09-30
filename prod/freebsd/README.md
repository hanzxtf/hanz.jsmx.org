

# init

Ensure `www` has a home:

```
pw usermod www -d /home/www
```

If not:

```
mkdir -p /home/www
chown www:www /home/www
```

set shell for www:

```
pw unlock www
chsh -s /bin/sh www
```

## set up deploy keys

as root.

```
install -d -m 700 -o www -g www /home/www/.ssh
ssh-keygen -t ed25519 -f /home/www/.ssh/deploy -N ""
cat /home/www/.ssh/deploy.pub
```

Add this key to GitHub:

- Repo → Settings → Deploy keys
- Add key
- ✔ Read access

ssh config for github:

```
cat > /home/www/.ssh/config <<EOF
Host github.com
  IdentityFile /home/www/.ssh/deploy
  IdentitiesOnly yes
  StrictHostKeyChecking accept-new
EOF
```

fix ownership:

```
chown www:www /home/www/.ssh/deploy*
chown www:www /home/www/.ssh/config
chmod 600 /home/www/.ssh/deploy
chmod 644 /home/www/.ssh/deploy.pub
chmod 600 /home/www/.ssh/config
```

### sanity check

```
su - www -c "ssh -T git@github.com"
```

it should return something like:

```
Hi fivehanz/hanz.jsmx.org! You've successfully authenticated, but GitHub does not provide shell access.
```

## clone repo


clone the repo to the `/usr/local/www/wagtail` directory

```
GIT_SSH_COMMAND="ssh -i /home/www/.ssh/deploy -o IdentitiesOnly=yes" \
git clone git@github.com:YOUR_USER/YOUR_REPO.git /usr/local/www/wagtail
```

fix ownerships:

```
chown -R www:www /usr/local/www/wagtail
```

## ssl certs

i use cloudflare origin certs with 15 year validity

```
install -d -m 755 /usr/local/etc/ssl

chmod 600 /usr/local/etc/ssl/cf-origin.key
chmod 644 /usr/local/etc/ssl/cf-origin.pem
```

# setup pkgs

```
pkg install --yes nginx litestream just python311 uv
```

# environment and secrets

Start from the template and fill in every empty value:

```
cp .env.prod.example .env.prod
python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # -> SECRET_KEY
```

`.env.prod` is ignored by git. Production refuses to start if a required value
is missing or still a placeholder, and the error names the setting and points
back at this file.

| Setting | What to put |
| --- | --- |
| `SECRET_KEY` | at least 50 random characters, unique to this server |
| `DJANGO_DEBUG` | `false` |
| `ALLOWED_HOSTS` | comma-separated real hostnames, never `*` |
| `CSRF_TRUSTED_ORIGINS` | comma-separated `https://` origins |
| `WAGTAILADMIN_BASE_URL` | this site's `https://` origin |
| `DATABASE_PATH` | the SQLite file Litestream replicates, e.g. `/var/db/wagtail/database.db` |
| `AWS_*` | media storage credentials |
| `LITESTREAM_*` | replication credentials and bucket |
| `DEFAULT_FROM_EMAIL` | a real address, so form notifications come from the site |
| `EMAIL_HOST` / `EMAIL_PORT` | the relay this server can reach; a local MTA on port 25 is fine |

If mail fails, the submission is still stored and the error is logged, so a mail
outage never turns a visitor's submission into an error page.

Then install it where the rc.d service reads it (`root:www`, mode 640):

```
just setup-env
```

`just prod-setup` runs this as part of the first deploy.

If the service refuses to start, `/var/log/wagtail.log` names the setting that
is missing or wrong.
