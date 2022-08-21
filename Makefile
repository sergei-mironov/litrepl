.DEFAULT_GOAL = all
VERSION = $(shell python3 setup.py --version)
WHEEL = dist/litrepl-$(VERSION)-py3-none-any.whl
PY = $(shell find -name '*\.py' | grep -v version.py)
# TEX = $(shell find docs -name '*\.tex')
# TESTS = $(shell find tests -name '*\.py')

$(WHEEL): $(PY)
	test -n "$(VERSION)"
	rm -rf build dist || true
	python3 setup.py sdist bdist_wheel
	test -f $@

.PHONY: version
version:
	@echo $(VERSION)

.PHONY: wheel
wheel: $(WHEEL)

.PHONY: all
all: wheel

