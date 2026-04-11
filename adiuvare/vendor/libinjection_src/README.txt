Local libinjection source drop for the rebuild.

This is just the first vendor pass.
The wrapper can already try a local dll, but the payload signal still uses
the fallback path when the binary is missing or broken.
