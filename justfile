# Compile every typst document in docs/ into output/
compile:
    @mkdir -p output
    @for f in docs/*.typ; do \
        echo "typst compile $f"; \
        typst compile "$f" "output/$(basename "${f%.typ}").pdf"; \
    done

# Remove generated output
clean:
    @rm -rf output

# Run the platform correctness and reproducibility suite.
test:
    PYTHONPATH=src python -m unittest discover -s tests -v

# Validate every checked-in development benchmark source.
validate-benchmarks:
    PYTHONPATH=src python -m tsp_perm_ea_bench.cli.main validate --manifest benchmarks/manifest.json

# Preview the development smoke task matrix without writing results.
smoke-plan:
    PYTHONPATH=src python -m tsp_perm_ea_bench.cli.main batch --config configs/development-smoke.json --dry-run
