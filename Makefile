.DEFAULT_GOAL = all
VERSION = $(shell python3 setup.py --version 2>/dev/null)
WHEEL = dist/litrepl-$(VERSION)-py3-none-any.whl
PY = $(shell find -name '*\.py' | grep -v semver.py | grep -v revision.py)
VIM = $(shell find -name '*\.vim')
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

$(WHEEL): $(PY) Makefile .stamp_test
	test -n "$(VERSION)"
	rm -rf build dist || true
	python3 setup.py sdist bdist_wheel
	test -f $@

.PHONY: wheel # Build Python wheel (the DEFAULT target)
wheel: $(WHEEL)

.PHONY: version # Print the version
version:
	@echo $(VERSION)

.PHONY: upload # Upload wheel to Pypi.org (./_token.pypi is required)
upload: $(WHEEL)
	twine upload \
		--username __token__ \
		--password $(shell cat _token.pypi) \
		dist/*

.PHONY: all
all: wheel

