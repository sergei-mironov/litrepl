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

.stamp_test: $(PY) $(VIM) $(TESTS) Makefile python/bin/litrepl
	LITREPL_BIN="`pwd`/python/bin" \
	LITREPL_ROOT=`pwd` \
	sh $(TESTS)
	touch $@

.PHONY: man # Build a manpage
man: $(MAN)
$(MAN): $(PY) Makefile python/bin/litrepl doc/description.md
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
.stamp_docs: $(PY) $(DOCS) $(TOP) python/bin/litrepl
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
	@cat Makefile | sed -n 's@^.PHONY: \([a-z]\+\) # \(.*\)@    \1:   \2@p' | column -t -l2

.PHONY: test # Run the test script (./sh/runtests.sh)
test: .stamp_test

.stamp_readme: $(PY)
	cp README.md _README.md.in
	cat _README.md.in \
	|litrepl --foreground --exception-exitcode=100 --result-textwidth=100 \
			--ai-interpreter=- \
			--sh-interpreter=- \
			eval-sections \
	>README.md
	touch $@

.PHONY: readme # Update code sections in the README.md
readme: .stamp_readme

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

.PHONY: all
all: wheel

