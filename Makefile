.PHONY: setup compile lint query search serve clean status daily

setup:
	bash scripts/bootstrap.sh

up:
	ollama serve &
	@echo "Ollama started on :11434"

compile:
	./tools/kb compile --incremental

compile-full:
	./tools/kb compile --full

lint:
	./tools/kb lint --check --suggest

fix:
	./tools/kb lint --fix

serve:
	./tools/kb serve --port 8080

status:
	./tools/kb status

daily:
	bash scripts/daily_workflow.sh

clean:
	rm -rf .compile_state.json .search_index.json
	@echo "Cleaned build state. Wiki and raw data preserved."
