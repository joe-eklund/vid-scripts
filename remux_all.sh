for f in *.mkv; do
    python remux.py "$f"
done
