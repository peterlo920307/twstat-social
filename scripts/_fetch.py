"""Download helpers shared by the three scripts in this directory.

This is not a script. It holds what every download here has to do and what the
first versions of the scripts did not: say who is asking, retry what is worth
retrying, refuse a payload that is not the spreadsheet that was asked for, and
never leave half a file under the final name.

The last two matter because Academia Sinica's server sits behind a web
application firewall that can answer with HTTP 200 and an HTML error page. The
earlier scripts saved that page as ``Mt468.xls`` and reported success.
"""

import contextlib
import http.client
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile
from typing import NamedTuple

USER_AGENT = "twstat-social/0.1 (+https://github.com/peterlo920307/twstat-social)"

# The first bytes of each format. An .xls is an OLE2 compound document and an
# .xlsx is a zip archive; an HTML error page is neither.
MAGIC = {
    ".xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    ".xlsx": b"PK\x03\x04",
}

# Seconds to wait before each retry. Three retries, then give up.
BACKOFF = (1, 4, 16)


class FetchError(Exception):
    """A download failed, or returned something other than the file asked for."""


class Response(NamedTuple):
    """The parts of an HTTP response the checks below need."""

    payload: bytes
    content_type: str | None
    content_length: str | None
    final_url: str


def get(url, timeout):
    """Fetch ``url``, retrying failures that are likely to be temporary.

    Connection failures, timeouts, HTTP 5xx and a body cut short are retried
    after 1, 4 and 16 seconds. Any other HTTP error, 403 and 404 included, is
    reported at once: asking again will not change the answer, and a firewall
    that has already refused us should not be pressed.

    Args:
        url: The address to fetch.
        timeout: Seconds to wait on the socket for each attempt.

    Returns:
        The body and the headers the payload checks use.

    Raises:
        FetchError: The request failed and retrying did not help, or should
            not be tried.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for pause in (*BACKOFF, None):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return Response(
                    response.read(),
                    response.headers.get("Content-Type"),
                    response.headers.get("Content-Length"),
                    response.geturl(),
                )
        except urllib.error.HTTPError as error:
            # HTTPError is a URLError, so it has to be caught first.
            if error.code < 500 or pause is None:
                raise FetchError(f"{url}: HTTP {error.code} {error.reason}") from error
            reason = f"HTTP {error.code}"
        # TimeoutError and ConnectionError are what URLError wraps when they
        # happen while connecting; while reading the body they arrive bare.
        except (
            urllib.error.URLError,
            http.client.IncompleteRead,
            TimeoutError,
            ConnectionError,
        ) as error:
            if pause is None:
                raise FetchError(f"{url}: {type(error).__name__}: {error}") from error
            reason = type(error).__name__
        print(f"    {reason} from {url}; retrying in {pause}s", file=sys.stderr, flush=True)
        time.sleep(pause)
    raise AssertionError("unreachable: the last attempt either returns or raises")


def kind(name):
    """Return ``".xls"`` or ``".xlsx"`` for a file name, whatever its case.

    Seventeen of the compendium's tables are named ``.XLS``.

    Raises:
        ValueError: The name is neither.
    """
    extension = os.path.splitext(name)[1].lower()
    if extension not in MAGIC:
        raise ValueError(f"{name} is not an .xls or .xlsx file")
    return extension


def check_spreadsheet(response, url, extension):
    """Raise unless ``response`` holds a whole spreadsheet of the given kind.

    Args:
        response: What :func:`get` returned.
        url: The address that was asked for, for the message.
        extension: ``".xls"`` or ``".xlsx"``.

    Raises:
        FetchError: The body does not start the way that format starts, or is
            not as long as the server said it would be.
    """
    payload = response.payload
    problem = None
    if not payload.startswith(MAGIC[extension]):
        problem = f"this is not an {extension} file"
    elif response.content_length is not None and response.content_length.strip().isdigit():
        declared = int(response.content_length)
        if declared != len(payload):
            problem = f"the server announced {declared} bytes and sent {len(payload)}"
    if problem:
        raise FetchError(
            f"{url} did not return the spreadsheet asked for: {problem}.\n"
            f"      content type {response.content_type!r}, {len(payload)} bytes,"
            f" starting {payload[:32]!r}\n"
            f"      final URL {response.final_url}\n"
            "      A server behind a firewall can answer 200 with an error page;"
            " open the URL in a browser to see what it sent."
        )


def save(payload, dest):
    """Write ``payload`` to ``dest`` so that ``dest`` is never half-written.

    The bytes go to ``dest + ".part"`` first and are renamed over ``dest`` only
    once they are all on disk. If anything interrupts the write, Ctrl-C
    included, the ``.part`` file is removed and ``dest`` is left as it was.
    """
    part = dest + ".part"
    try:
        with open(part, "wb") as handle:
            handle.write(payload)
        os.replace(part, dest)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(part)
        raise


def download(url, dest, timeout):
    """Fetch the spreadsheet at ``url``, check it, and save it as ``dest``.

    The format expected is taken from the extension of ``dest``.

    Returns:
        The bytes that were saved.

    Raises:
        FetchError: The download failed or was not the spreadsheet asked for.
            Nothing is written in that case.
    """
    response = get(url, timeout)
    check_spreadsheet(response, url, kind(dest))
    save(response.payload, dest)
    return response.payload


def looks_complete(path):
    """Say whether a spreadsheet already on disk can be kept rather than fetched.

    Anything :func:`save` wrote is complete. This check is for files left by the
    earlier versions of these scripts, which wrote in place and could leave an
    HTML error page or a truncated file under the final name.

    The file has to begin and end the way its format does. An OLE2 compound
    document is a 512-byte header followed by whole sectors of 512 or 4096
    bytes, so its size is a multiple of 512, as all 649 of the digitised
    compendium's files are. An .xlsx is a zip archive, whose directory is at the end, and a
    truncated one does not have it. Neither test proves a file is correct;
    ``scripts/download_raw.py`` checks the published tables against checksums
    for that.
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as handle:
            head = handle.read(8)
    except OSError:
        return False
    extension = kind(path)
    if not head.startswith(MAGIC[extension]):
        return False
    if extension == ".xls":
        return size % 512 == 0
    return zipfile.is_zipfile(path)


def require_writable(directory):
    """Create ``directory`` if need be, and stop now if files cannot go in it.

    Better to find out before the first download than after the last.

    The test writes a file of its own rather than using ``tempfile``: on
    Windows, ``tempfile`` treats "access denied" as a name collision and keeps
    trying new names, which in a directory the user may not write to means it
    never returns.

    Raises:
        SystemExit: The directory cannot be created or written to.
    """
    probe = os.path.join(directory, f".write-test-{os.getpid()}")
    try:
        os.makedirs(directory, exist_ok=True)
        with open(probe, "wb"):
            pass
        os.remove(probe)
    except OSError as error:
        raise SystemExit(f"cannot write to {directory}: {error}") from error


def utf8_console():
    """Print UTF-8 whatever the console's code page.

    On Windows, output redirected to a file or pipe defaults to the ANSI code
    page, usually cp1252, which cannot encode the table titles and era names
    these scripts print.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")
