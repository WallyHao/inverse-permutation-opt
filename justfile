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
