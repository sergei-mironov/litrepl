.DEFAULT_GOAL = all
REVISION = $(shell git rev-parse HEAD | cut -c 1-7)
VERSION = $(shell python3 setup.py --version 2>/dev/null)
WHEEL_REV = _dist/litrepl-$(VERSION)-$(REVISION)-py3-none-any.whl
WHEEL = dist/litrepl-$(VERSION)-py3-none-any.whl
PY = $(shell find -name '*\.py' | grep -v semver.py | grep -v revision.py)
VIM = $(shell find vim -name '*\.vim')
VIMB_REV = _dist/vim-litrepl-$(VERSION)-$(REVISION).tar.gz
PAPER_TAR_GZ = paper/tex/paper-$(VERSION)-$(REVISION).tar.gz
TESTS = ./sh/runtests.sh

.stamp_test: $(PY) $(VIM) $(TESTS) Makefile python/bin/litrepl
	LITREPL_BIN="`pwd`/python/bin" \
	LITREPL_ROOT=`pwd` \
	sh $(TESTS)
	touch $@

.PHONY: help # Print help
help:
	@echo "LitREPL is a macroprocessing Python library for Litrate programming and code execution"
	@echo Build targets:
	@cat Makefile | sed -n 's@^.PHONY: \([a-z_-]\+\) # \(.*\)@    \1:   \2@p' | sort | column -t -l2

.PHONY: test # Run the test script (./sh/runtests.sh)
test: .stamp_test

.stamp_readme: $(PY)
	cp README.md _README.md.in
	cat _README.md.in \
	|litrepl --foreground --exception-exitcode=100 --result-textwidth=100 \
			--ai-interpreter=- \
			--sh-interpreter=- \
			eval-sections \
	|litrepl --foreground \
			--ai-interpreter=- \
			--python-interpreter=- \
			--sh-interpreter=/bin/sh \
			eval-sections '$$' \
	>README.md
	touch $@

.PHONY: readme # Update code sections in the README.md
readme: .stamp_readme

$(WHEEL_REV): $(PY) Makefile .stamp_test .stamp_readme
	mkdir -p $$(dirname $@) || true
	test -n "$(VERSION)"
	rm -rf build dist || true
	python3 setup.py sdist bdist_wheel
	test -f $(WHEEL)
	cp $(WHEEL) $(WHEEL_REV)

.PHONY: wheel # Build Python wheel (the DEFAULT target)
wheel: $(WHEEL_REV)

.PHONY: vimbundle # Build Vim bundle
vimbundle: $(VIMB_REV)

$(VIMB_REV): $(VIM)
	mkdir -p $$(dirname $@) || true
	rm -rf build/vim || true
	mkdir -p build/vim/plugin
	cp -r vim/plugin/*vim build/vim/plugin
	sed -i "s/version-to-be-filled-by-the-packager/$(VERSION)+g$(REVISION)/g" \
		build/vim/plugin/litrepl.vim
	tar -czvf $@ -C build/vim plugin

.PHONY: version # Print the version
version:
	@echo $(VERSION)+g$(REVISION)

.PHONY: dist # Build Python and Vim packages
dist: $(WHEEL_REV) $(VIMB_REV)

.PHONY: upload # Upload Python wheel to Pypi.org (./_token.pypi is required)
upload: $(WHEEL_REV) $(VIMB_REV)
	twine upload \
		--username __token__ \
		--password $(shell cat _token.pypi) \
		dist/*

.PHONY: paper-md
paper-md: paper/md/paper.pdf
paper/md/paper.pdf: paper/md/paper.md ./paper/tex/pic.png ./paper/md/input.tex
	docker run --rm --volume $$PWD/paper/md:/data --user $(id -u):$(id -g) --env JOURNAL=joss openjournals/inara

.PHONY: paper-quick # Compile the paper PDF out of its LaTeX source without re-evaluation
.PHONY: pq
paper-quick: ./paper/tex/paper_quick.pdf
pq: ./paper/tex/paper_quick.pdf
./paper/tex/paper_quick.pdf: ./paper/tex/paper.tex ./paper/tex/pic.pdf ./paper/tex/paper.bib
	cd ./paper/tex && \
	cp paper.tex paper_quick.tex && \
	latexmk -shell-escape -pdf -latex=pdflatex paper_quick.tex && \
	touch `basename $@`

.PHONY: paper # Check and compile the paper PDF out of its LaTeX source
.PHONY: p
paper: ./paper/tex/paper.pdf
p: ./paper/tex/paper.pdf
./paper/tex/paper.pdf: ./paper/tex/paper_checked.tex ./paper/tex/pic.pdf ./paper/tex/paper.bib
	cd paper/tex && \
	latexmk -shell-escape -pdf -latex=pdflatex paper_checked.tex && \
	cp paper_checked.pdf paper.pdf
./paper/tex/paper_checked.tex: ./paper/tex/paper.tex
	cd paper/tex && \
	cat paper.tex | litrepl \
		--filetype=latex --ai-interpreter=- \
		--pending-exitcode=3 --irreproducible-exitcode=4 \
		--foreground >paper_checked.tex

.PHONY: paper.tar.gz
paper.tar.gz: $(PAPER_TAR_GZ)
$(PAPER_TAR_GZ): ./paper/tex/paper.pdf
	tar -czvf $@ -C paper/tex paper.tex pic.pdf paper.bib paper.bbl


.PHONY: all
all: wheel

