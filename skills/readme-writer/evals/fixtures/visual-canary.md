# Lantern Works

> [!NOTE]
> This page is the home of Lantern Works, a small studio that builds command-line tools for people who keep long-lived notes in plain text.

> [!IMPORTANT]
> Everything here is free to use. Each tool lives in its own repository, and each repository has its own license, issue tracker and release notes.

> [!TIP]
> If you only read one thing, read the table below.

We started Lantern Works because our own notes kept outgrowing the tools we used to write them. Over the years the notes became a small archive: meeting logs, reading lists, recipes, half-finished essays, and a decade of daily journals. Every tool here began as a script that fixed one annoyance in that archive, and every one of them was rewritten at least twice before we were willing to share it.

The tools share a few habits. They read and write plain text, they never hold your notes in a database you cannot open with an editor, they work offline, and they print what they are about to change before they change it. None of them phones home. Most of them run in under a second on an archive of fifty thousand files, and the ones that do not will tell you why.

We are two people, we answer issues on weekends, and we would rather ship one tool that works than three that almost do. That is also why the list below is short.

A note on versions: every tool follows semantic versioning, keeps a changelog in its repository, and supports the two most recent releases of macOS, Debian and Ubuntu. Older systems usually work, but we do not test them, and we close issues about them only when a pull request comes with the fix. Windows support depends on the tool; each README says which parts run there and which do not.

## Where to go

| If you want to | Open | Notes |
|---|---|---|
| Find a note by what it says | [lantern-grep](https://example.com/lantern-grep) | Full-text search with `--since`, `--tag` and `--path` filters |
| Rename notes and fix every link | [lantern-mv](https://example.com/lantern-mv) | Prints the plan first |
| Turn a folder into a static site | [lantern-site](https://example.com/lantern-site) | No JavaScript |

## Commands

- `lantern-grep --since 2020-01-01 --tag recipe --path journal/ "sourdough starter"`
- `lantern-mv notes/old-name.md notes/new-name.md --update-links --dry-run`
- `lantern-site build --out public/ --theme plain`

## Configuration

| Key | Default | Example |
|---|---|---|
| `archive_root` | `~/notes` | `lantern-grep --config ~/.config/lantern/config.toml --archive-root ~/Documents/notes-archive-2014-present` |
