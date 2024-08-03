.DEFAULT_GOAL = all
VERSION = $(shell python3 setup.py --version 2>/dev/null)
REVISION = $(shell git rev-parse HEAD | cut -c 1-7)
WHEEL = dist/litrepl-$(VERSION)-py3-none-any.whl
PY = $(shell find -name '*\.py' | grep -v semver.py | grep -v revision.py)
VIM = $(shell find -name '*\.vim')
VIMB = dist/vim-litrepl-$(VERSION).tar.gz
TESTS = ./sh/test.sh

.stamp_test: $(PY) $(VIM) $(TESTS) Makefile python/bin/litrepl
	LITREPL_BIN="`pwd`/python/bin" \
	LITREPL_ROOT=`pwd` \
	sh ./sh/test.sh
	touch $@

.PHONY: help # Print help
help:
	@echo "LitREPL is a macroprocessing Python library for Litrate programming and code execution"
	@echo Build targets:
	@cat Makefile | sed -n 's@^.PHONY: \([a-z]\+\) # \(.*\)@    \1:   \2@p' | column -t -l2

.PHONY: test # Run the test script (./sh/test.sh)
test: .stamp_test

.stamp_readme: $(PY)
	cp README.md _README.md.in
	cat _README.md.in | \
		litrepl --foreground --exception-exit=100 --result-textwidth=100 \
		eval-sections >README.md
	touch $@

.PHONY: readme # Update code sections in the README.md
readme: .stamp_readme

$(WHEEL): $(PY) Makefile .stamp_readme
	test -n "$(VERSION)"
	rm -rf build dist || true
	python3 setup.py sdist bdist_wheel
	test -f $@

.PHONY: wheel # Build Python wheel (the DEFAULT target)
wheel: $(WHEEL)

.PHONY: vimbundle # Build Vim bundle
vimbundle: $(VIMB)

$(VIMB): $(VIM)
	mkdir -p $$(dirname $(VIMB)) || true
	rm -rf build/vim || true
	mkdir -p build/vim
	cp -r vim/plugin build/vim
	sed -i "s/version-to-be-filled-by-the-packager/$(VERSION)+g$(REVISION)/g" \
		build/vim/plugin/litrepl.vim
	tar -czvf $@ -C build/vim plugin

.PHONY: version # Print the version
version:
	@echo $(VERSION)+g$(REVISION)

.PHONY: dist # Build Python and Vim packages
dist: $(WHEEL) $(VIMB)

.PHONY: upload # Upload Python wheel to Pypi.org (./_token.pypi is required)
upload: $(WHEEL) $(VIMB)
	twine upload \
		--username __token__ \
		--password $(shell cat _token.pypi) \
		dist/*

.PHONY: all
all: wheel

