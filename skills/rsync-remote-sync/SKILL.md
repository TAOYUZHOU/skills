---
name: rsync-remote-sync
description: Pull or push files and directories between local and remote servers via rsync over SSH. Use when syncing code, models, datasets, or project trees across machines (AutoDL, EC2, Vast.ai, lab servers), including custom SSH ports, PEM keys, dry-run preview, exclude rules, and multi-job config files.
metadata:
  short-description: rsync over SSH between local and remote servers
  migrated-from: https://github.com/TAOYUZHOU/rsync-pull-from-remote
---

# Rsync Remote Sync

Use this skill when the user wants to copy files or directories between machines with `rsync` over SSH — for example pulling a remote repo to local, pushing checkpoints to a GPU server, or syncing experiment artifacts between AutoDL, EC2, and lab hosts.

Prefer the bundled scripts over ad-hoc one-liners. They handle SSH port, identity file, dry-run, excludes, and optional password auth consistently.

## Dependencies

```bash
sudo apt install rsync openssh-client
# Non-interactive password auth only:
sudo apt install sshpass
```

## Workflow

1. Confirm direction: **pull** (remote → local) or **push** (local → remote).
2. Verify SSH connectivity first:

```bash
ssh -i /path/to/key.pem -p PORT user@host "echo SSH_OK"
```

3. For large trees, run a **dry-run** before the real sync.
4. Run the appropriate script from this skill's `scripts/` directory.
5. After sync, spot-check size/file count on the destination side.

## Pull (remote → local)

```bash
SKILL_ROOT="/root/autodl-tmp/taoyuzhou/skills/skills/rsync-remote-sync"

# Key auth, custom port
"$SKILL_ROOT/scripts/rsync_pull_from_remote.sh" \
  -i /path/to/key.pem -p 22 \
  ubuntu@ec2.example.com:/home/ubuntu/project/ \
  /local/dest/

# Preview only
"$SKILL_ROOT/scripts/rsync_pull_from_remote.sh" -n \
  -i /path/to/key.pem -p 22 \
  ubuntu@host:/remote/path/ /local/dest/

# Exclude heavy or generated dirs
"$SKILL_ROOT/scripts/rsync_pull_from_remote.sh" \
  -i /path/to/key.pem -p 42994 \
  -e .git -e __pycache__ -e .pytest_cache \
  root@connect.example.com:/root/project/ \
  /home/ubuntu/project/
```

## Push (local → remote)

```bash
SKILL_ROOT="/root/autodl-tmp/taoyuzhou/skills/skills/rsync-remote-sync"

# Upload a single file
"$SKILL_ROOT/scripts/rsync_push_to_remote.sh" \
  -i /path/to/key.pem -p 42994 \
  ./model.pt root@host:/remote/path/model.pt

# Upload directory contents
"$SKILL_ROOT/scripts/rsync_push_to_remote.sh" \
  -i /path/to/key.pem -p 42994 \
  ./local_dir/ root@host:/remote/dir/
```

## Path Semantics

Trailing slashes matter:

| Spec | Effect |
|------|--------|
| `host:/dir/` | Sync **contents of dir** into destination |
| `host:/dir` | Create/use a **dir subdirectory** at destination |
| `./dir/ host:/dir/` | Push **dir contents** into remote dir |
| `./file host:/dir/file` | Push one file to an explicit remote path |

## Config Jobs (optional)

For repeatable syncs, copy the example config and run by job name:

```bash
cp assets/rsync_jobs.example.conf /path/to/rsync_jobs.conf
# edit rsync_jobs.conf — never commit passwords

"$SKILL_ROOT/scripts/rsync_pull_from_remote.sh" \
  --config /path/to/rsync_jobs.conf --job my_job
```

See `assets/rsync_jobs.example.conf` for the job schema (`user`, `host`, `port`, `source`, `dest`, `identity`, `exclude`, `delete`, `password_auth`).

## CLI Reference

### `rsync_pull_from_remote.sh`

| Flag | Meaning |
|------|---------|
| `-p, --port` | SSH port (default 22) |
| `-i, --identity` | SSH private key path |
| `-e, --exclude` | Exclude pattern (repeatable) |
| `-n, --dry-run` | Preview only |
| `-D, --delete` | Delete local extras not on remote (use with care) |
| `-P, --password-auth` | Allow password auth |
| `-c, --config` / `-j, --job` | Run from config file |

### `rsync_push_to_remote.sh`

Same flags except config jobs are pull-only today.

## Security

- **Never** write passwords into scripts, configs, or git repos.
- Prefer SSH keys: `ssh-copy-id -p PORT user@host`
- For `SSHPASS`, set only in the current shell and `unset SSHPASS` afterward:

```bash
SSHPASS='...' "$SKILL_ROOT/scripts/rsync_pull_from_remote.sh" -P -p 42994 root@host:/src/ /dst/
unset SSHPASS
```

## Agent Guidelines

- Always test SSH before starting a large rsync.
- Default to dry-run (`-n`) when the user has not confirmed overwrite behavior.
- Avoid `--delete` unless the user explicitly asks for mirror semantics.
- For multi-GB trees, use `--info=progress2` (already enabled in scripts) and expect long runtimes.
- If the user gives a PEM path and host, construct the command with `-i` rather than inventing raw rsync flags.

## Migration Note

This skill replaces the standalone repo [TAOYUZHOU/rsync-pull-from-remote](https://github.com/TAOYUZHOU/rsync-pull-from-remote). Use the scripts under `scripts/` in this skill directory going forward.
