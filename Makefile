SRC := main.py

all: install run

install:
	uv sync

run:
	uv run python main.py

help:
	uv run python main.py -h

debug:
	uv run python -m pdb main.py

test:
	uv run pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache

fclean: clean
	uv cache clean
	rm -rf .venv

lint:
	uv run flake8 $(SRC)
	uv run mypy $(SRC) --warn-return-any --warn-unused-ignores \
					   --ignore-missing-imports --disallow-untyped-defs \
					   --check-untyped-defs

lint-strict:
	uv run flake8 $(SRC)
	uv run mypy $(SRC) --strict

re: fclean all

.PHONY: all install run help debug clean fclean lint lint-strict re
