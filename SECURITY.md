# Security

`twstat` reads spreadsheet files and, through the scripts in `scripts/`,
downloads them from two academic servers. Those are the only places it touches
anything outside its own process.

If you find a way for a crafted spreadsheet or a server response to make it do
something other than read data — write outside the directory it was given, run
code, or accept a file that is not what it claims to be — please do not open a
public issue. Use GitHub's private vulnerability reporting on this repository
("Report a vulnerability" under the Security tab), or contact the maintainer
through their GitHub profile, [@peterlo920307](https://github.com/peterlo920307).

The download scripts already refuse a payload that is not a spreadsheet and check
the source files against `docs/raw_manifest.json`; a way around either of those
is exactly the kind of report this is for.

Only the latest version on `main` is maintained.
