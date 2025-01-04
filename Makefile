.DEFAULT_GOAL = all
REVISION = $(shell git rev-parse HEAD | cut -c 1-7)
VERSION = $(shell python3 setup.py --version 2>/dev/null)
WHEEL_REV = _dist/litrepl-$(VERSION)-$(REVISION)-py3-none-any.whl
WHEEL = dist/litrepl-$(VERSION)-py3-none-any.whl
PY = $(shell find -name '*\.py' | grep -v semver.py | grep -v revision.py)
VIM = $(shell find vim -name '*\.vim')
VIMB_REV = _dist/vim-litrepl-$(VERSION)-$(REVISION).tar.gz
TESTS = ./sh/runtests.sh
MAN = man/litrepl.1
DOCS = $(shell find docs -name '*\.md' | grep -v static | grep -v examples)
TOP = flake.nix default.nix Makefile
EXAMPLES = docs/examples/example.md docs/examples/example.tex

.PHONY: examples # Build examples
examples: .stamp_examples
.stamp_examples: $(PY) $(TOP) $(EXAMPLES)
	set -e ; \
	for e in $(EXAMPLES) ; do \
		cat $$e | litrepl --foreground \
											--exception-exitcode=100 \
											--result-textwidth=0 \
											eval-sections \
											>$$e.new ; \
		mv $$e.new $$e ; \
	done
	( cd docs/examples && latexmk \
		-shell-escape -pdf -interaction=nonstopmode \
	  -latex=pdflatex --halt-on-error -outdir=_build  example.tex \
		&& cp _build/example.pdf . ; )


.PHONY: man # Build a manpage
man: $(MAN)
$(MAN): $(PY) Makefile python/bin/litrepl docs/static/description.md
	argparse-manpage --module litrepl.main \
		--author 'Sergei Mironov' \
 	  --author-email 'sergei.v.mironov@proton.me' \
		--url 'https://github.com/sergei-mironov/litrepl' \
		--project-name 'litrepl' \
		--description "$$(pandoc --to=plain docs/static/description.md -o -)" \
		--version $(VERSION) \
		--object=AP >$@

.PHONY: docs # Build the MkDocs documentation
docs: .stamp_docs_deploy
.stamp_docs: $(PY) $(DOCS) $(TOP) .stamp_examples python/bin/litrepl
	cp $(TOP) docs/static
	set -e; \
	for d in $(DOCS) ; do \
		echo "Evaluating $$d" ; \
		cat $$d | litrepl --foreground \
				--exception-exitcode=100 \
				--result-textwidth=0 \
				--ai-interpreter=- \
				--sh-interpreter=- \
				eval-sections \
		>$$d.new ; \
		mv $$d.new $$d ; \
	done
	mkdocs build
	touch $@
.stamp_docs_deploy: .stamp_docs
	mkdocs gh-deploy
	touch $@

.PHONY: help # Print help
help:
	@echo "LitREPL is a macroprocessing Python library for Litrate programming and code execution"
	@echo Build targets:
	@cat Makefile | sed -n 's@^.PHONY: \([a-z_]\+\) # \(.*\)@    \1:   \2@p' | sort | column -t -l2

.PHONY: test # Run the test script (./sh/runtests.sh)
test: .stamp_test

.stamp_test: $(PY) $(VIM) $(TESTS) Makefile python/bin/litrepl
	LITREPL_BIN="`pwd`/python/bin" \
	LITREPL_ROOT=`pwd` \
	sh $(TESTS)
	touch $@

.PHONY: readme # Update code sections in the README.md
readme: .stamp_readme

.stamp_readme: $(PY) $(TOP) .stamp_examples
	cat README.md | litrepl --foreground --exception-exitcode=100 --result-textwidth=100 \
										 		--ai-interpreter=- \
												--sh-interpreter=- \
												eval-sections \
	>README.md.new
	mv README.md.new README.md
	touch $@

$(WHEEL_REV): $(PY) Makefile .stamp_test .stamp_readme $(MAN)
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

.PHONY: paper-quick # Compile the paper PDF out of its LaTeX source without re-evaluation
.PHONY: pq
paper-quick: ./paper/paper_quick.pdf
pq: ./paper/paper_quick.pdf
./paper/paper_quick.pdf: ./paper/paper.tex ./paper/pic.svg ./paper/paper.bib
	cd ./paper && \
	cp paper.tex paper_quick.tex && \
	latexmk -shell-escape -pdf -latex=pdflatex paper_quick.tex && \
	touch `basename $@`

.PHONY: paper # Check and compile the paper PDF out of its LaTeX source
.PHONY: p
paper: ./paper/paper_checked.pdf
p: ./paper/paper_checked.pdf
./paper/paper_checked.pdf: ./paper/paper_checked.tex ./paper/pic.svg ./paper/paper.bib
	cd paper && \
	latexmk -shell-escape -pdf -latex=pdflatex paper_checked.tex && \
	touch `basename $@`
./paper/paper_checked.tex: ./paper/paper.tex
	cd paper && \
	cat paper.tex | litrepl \
		--filetype=latex --ai-interpreter=- \
		--pending-exitcode=3 --irreproducible-exitcode=4 \
		--foreground >paper_checked.tex

.PHONY: all
all: wheel

