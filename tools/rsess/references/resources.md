# rsess Resources

> Load this when: an rsess question isn't covered by the local references — then consult the linked source.

- **tmux manual** — https://man.openbsd.org/tmux — authoritative reference for all tmux commands, formats, and options.
- **OpenSSH client configuration** — `man ssh_config` — the `Host`/`HostName`/`User`/`Port`/`ProxyJump`/`IdentityFile`/`ControlMaster` directives rsess relies on.
- **tmux source / static build guide** — https://github.com/tmux/tmux — the bundled binary is a static musl build of upstream tmux; build instructions are in the repository.
- **musl-cross for static binaries** — https://musl.cc/ — if a non-x86-64 static tmux is needed for a different remote architecture.
