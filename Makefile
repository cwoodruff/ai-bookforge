# AI Book Forge. BOOK is the folder holding book.yaml (default: this repo).
BOOK ?= .
GAPS ?= fail
FORGE := python3 -m forge --book $(BOOK)
.PHONY: init ingest briefs check status gaps stale stamp diagrams epub html pdf all final cover links test clean

init:   ; python3 -m forge --book $(BOOK) init
ingest: ; $(FORGE) ingest
briefs: ; $(FORGE) briefs
check:  ; $(FORGE) check
status: ; $(FORGE) status
epub:   ; $(FORGE) build epub
html:   ; $(FORGE) build html
pdf:    ; $(FORGE) build pdf
all:    ; $(FORGE) build epub html pdf
final:  ; $(FORGE) build epub html pdf --gaps $(GAPS)
gaps:   ; $(FORGE) gaps
stale:  ; $(FORGE) stale
stamp:  ; $(FORGE) stamp --all
diagrams: ; $(FORGE) diagrams
cover:  ; $(FORGE) cover
links:  ; $(FORGE) links
test:   ; python3 -m unittest discover -s tests -v
clean:  ; rm -rf $(BOOK)/build $(BOOK)/dist
